#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
"""
``DatazillaModelBase`` (and subclasses) are the public interface for all data
access.

"""
import datetime
import time
import json
import urllib
import zlib

from MySQLdb import IntegrityError
from collections import defaultdict

from django.conf import settings
from django.core.cache import cache


from . import utils
from .metrics import MetricsMethodFactory
from .sql.models import SQLDataSource


class DatazillaModelBase(object):
    """Base model class for all Datazilla models"""

    def __init__(self, project):
        self.project = project

        self.sources = {}
        for ct in self.CONTENT_TYPES:
            self.sources[ct] = SQLDataSource(project, ct)

        self.DEBUG = settings.DEBUG


    def __unicode__(self):
        """Unicode representation is project name."""
        return self.project


    def disconnect(self):
        """Iterate over and disconnect all data sources."""
        for src in self.sources.itervalues():
            src.disconnect()

    def get_project_cache_key(self, str_data):
        return "{0}_{1}".format(self.project, str_data)


class PushLogModel(DatazillaModelBase):
    """Public interface for all push logs"""

    CONTENT_TYPES = ["hgmozilla"]
    DEFAULT_PROJECT = "pushlog"

    # The "project" defaults to "pushlog" but you can pass in any
    # project name you like.

    def __init__(self, project=None, out=None, verbosity=0):
        super(PushLogModel, self).__init__(project or self.DEFAULT_PROJECT)
        self.out = out
        self.verbosity=verbosity
        self.reset_counts()


    @classmethod
    def create(cls, host=None, type=None, project=None):
        """
        Create all the datasource tables for this pushlog.

        ``hosts`` is an optional dictionary mapping contenttype names to the
        database server host on which the database for that contenttype should
        be created. Not all contenttypes need to be represented; any that
        aren't will use the default (``DATAZILLA_DATABASE_HOST``).

        ``types`` is an optional dictionary mapping contenttype names to the
        type of database that should be created. For MySQL/MariaDB databases,
        use "MySQL-Engine", where "Engine" could be "InnoDB", "Aria", etc. Not
        all contenttypes need to be represented; any that aren't will use the
        default (``MySQL-InnoDB``).


        """

        project = project or cls.DEFAULT_PROJECT

        for ct in cls.CONTENT_TYPES:
            SQLDataSource.create(
                 project, ct, host=host, db_type=type)

        return cls()


    def reset_counts(self):
        self.branch_count = 0
        self.pushlog_count = 0
        self.changeset_count = 0
        self.pushlog_skipped_count = 0
        self.changeset_skipped_count = 0


    @property
    def hg_ds(self):
        return self.sources["hgmozilla"]


    def get_all_branches(self):

        proc = 'hgmozilla.selects.get_all_branches'

        data_iter = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data_iter


    def get_branch_list(self, branch=None):
        # if a branch was specified, limit the list to only that branch
        # TODO: make a separate select for this case, instead of all
        branch_list = self.get_all_branches()

        if branch:
            branch_list=[x for x in branch_list if x["name"] == branch]
            if len(branch_list) < 1:
                self.println("Branch not found: {0}".format(branch))
                return

        return branch_list


    def get_all_pushlogs(self):

        proc = 'hgmozilla.selects.get_all_pushlogs'

        data_iter = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data_iter


    def get_all_changesets(self):

        proc = 'hgmozilla.selects.get_all_changesets'

        data_iter = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data_iter

    def get_changesets(self, pushlog_id):

        placeholders = [pushlog_id]
        proc = 'hgmozilla.selects.get_changesets'

        data_iter = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=placeholders,
            )

        return data_iter

    def get_branch_pushlog(self, branch_id, days_ago=None, numdays=None):
        """Retrieve pushes for a given branch for time range. If no
           time range is provided return all pushlogs for the branch."""

        data_iter = {}

        if days_ago and numdays:

            day_range = utils.get_day_range(days_ago, numdays)

            proc = 'hgmozilla.selects.get_branch_pushlog'

            data_iter = self.hg_ds.dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                placeholders=[branch_id, day_range['start'], day_range['stop']]
            )

        else:
            proc = 'hgmozilla.selects.get_all_branch_pushlogs'

            data_iter = self.hg_ds.dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                placeholders=[branch_id]
            )

        return data_iter


    def get_params(self, numdays, enddate=None):
        """
        Figure out the params to send to the pushlog queries.

        If enddate is None, then use today as the enddate.
        """

        if enddate:
            #create a proper datetime.date for calculation of startdate
            m, d, y = enddate.split("/")
            _enddate = datetime.date(month=int(m), day=int(d), year=int(y))
        else:
            _enddate = datetime.date.today()

        # calculate the startdate and enddate

        _startdate = _enddate - datetime.timedelta(days=numdays)

        params = {
            "full": 1,
            "startdate": _startdate.strftime("%m/%d/%Y"),
            }
        # enddate is optional.  the endpoint will just presume today,
        # if not given.
        if enddate:
            params.update({"enddate": enddate})

        return params


    def store_pushlogs(self, repo_host, numdays, enddate=None, branch=None):
        """
        Main entry point to store pushlogs for branches.

        If branch is None, then store pushlogs for ALL branches that we
        know about.

        If enddate is None, then use today as the enddate.

        """

        # fetch the list of known branches.
        branch_list = self.get_branch_list(branch)

        # parameters sent to the requests for pushlog data
        params = self.get_params(numdays, enddate)

        for br in branch_list:
            self.println(u"Branch: pushlogs for {0}".format(
                unicode(br["name"])).encode("UTF-8"),
                1
            )

            uri = "{0}/json-pushes".format(br["uri"])

            url = "https://{0}/{1}?{2}".format(
                repo_host,
                uri,
                urllib.urlencode(params),
                )

            self.println("URL: {0}".format(url), 1)

            # fetch the JSON content from the constructed URL.
            res = urllib.urlopen(url)
            json_data = res.read()
            try:
                pushlog_dict = json.loads(json_data)

                self._insert_branch_pushlogs(br["id"], pushlog_dict)
                self.branch_count = self.branch_count + 1

            except ValueError as e:
                self.println("--Skip branch {0}: push data not valid JSON: {1}".format(
                    branch,
                    json_data,
                    ))

        return {
            "branches": self.branch_count,
            "pushlogs_stored": self.pushlog_count,
            "changesets_stored": self.changeset_count,
            "pushlogs_skipped": self.pushlog_skipped_count,
            "changesets_skipped": self.changeset_skipped_count,
        }



    def _insert_branch_pushlogs(self, branch_id, pushlog_dict):
        """Loop through all the pushlogs and insert them."""
        for pushlog_json_id, pushlog in pushlog_dict.items():
            # make sure the pushlog_id isn't confused with a previous iteration
            self.println("    Pushlog {0}".format(pushlog_json_id), 1)

            placeholders = [
                pushlog_json_id,
                pushlog["date"],
                pushlog["user"],
                branch_id,
                ]
            try:
                pushlog_id = self._insert_data_and_get_id(
                    "set_pushlog",
                    placeholders=placeholders,
                    )

                # process the nodes of the pushlog
                self._insert_pushlog_changesets(pushlog_id, pushlog["changesets"])
                self.pushlog_count += 1

            except IntegrityError as e:
                self.println(e)
                self.println("--Skip dup- pushlog: {0}".format(
                    pushlog_json_id,
                ), 1)
                self.pushlog_skipped_count += 1
                # if a pushlog is skipped, then all its changesets are
                # also skipped as a result.
                self.changeset_skipped_count += len(pushlog["changesets"])


    def _insert_pushlog_changesets(self, pushlog_id, changeset_list):
        """Loop through all the changesets in a pushlog, and insert them."""

        for cs in changeset_list:
            self.println("        Changeset {0}".format(cs["node"]), 2)
            placeholders = [
                cs["node"],
                cs["author"],
                cs["branch"],
                cs["desc"],
                pushlog_id,
                ]

            try:
                self._insert_data_and_get_id(
                    "set_node",
                    placeholders=placeholders,
                    )
                self.changeset_count += 1

            except IntegrityError:
                self.println("--Skip changeset dup- pushlog: {0}, node: {1}".format(
                    pushlog_id,
                    cs["node"],
                    ))
                self.changeset_skipped_count += 1



    def _insert_data(self, statement, placeholders, executemany=False):

        return self.hg_ds.dhub.execute(
            proc='hgmozilla.inserts.' + statement,
            debug_show=settings.DEBUG,
            placeholders=placeholders,
            executemany=executemany,
            return_type='iter',
            )


    def _insert_data_and_get_id(self, statement, placeholders):

        self._insert_data(statement, placeholders)

        id_iter = self.hg_ds.dhub.execute(
            proc='hgmozilla.selects.get_last_insert_id',
            debug_show=settings.DEBUG,
            return_type='iter',
            )

        return id_iter.get_column_data('id')


    def println(self, val, level=0):
        """Write to out (possibly stdout) if verbosity meets the level."""
        if settings.DEBUG and self.out and self.verbosity >= level:
            self.out.write("{0}\n".format(str(val)))


class PerformanceTestModel(DatazillaModelBase):
    """Public interface to all data access for a performance project."""

    # content types that every project will have
    CONTENT_TYPES = ["perftest", "objectstore"]



    @classmethod
    def create(cls, project, hosts=None, types=None, cron_batch=None):
        """
        Create all the datasource tables for this project.

        ``hosts`` is an optional dictionary mapping contenttype names to the
        database server host on which the database for that contenttype should
        be created. Not all contenttypes need to be represented; any that
        aren't will use the default (``DATAZILLA_DATABASE_HOST``).

        ``types`` is an optional dictionary mapping contenttype names to the
        type of database that should be created. For MySQL/MariaDB databases,
        use "MySQL-Engine", where "Engine" could be "InnoDB", "Aria", etc. Not
        all contenttypes need to be represented; any that aren't will use the
        default (``MySQL-InnoDB``).

        ``cron_batch`` is which cron batch this project belongs to.  This will
        determine how often the project is automatically processed by various
        management commands.  None indicates it will not be automatically
        processed.  Other possible values are: small, medium, or large
        (generally depending on the size of the project, and how long a
        management command may spend on the projects of that size.)
        This only applies to the contenttype of "perftest".

        """
        hosts = hosts or {}
        types = types or {}

        for ct in cls.CONTENT_TYPES:
            SQLDataSource.create(
                project,
                ct,
                host=hosts.get(ct),
                db_type=types.get(ct),
                cron_batch=cron_batch if ct == "perftest" else None,
                )

        return cls(project=project)


    @classmethod
    def get_cron_batch_projects(cls, cron_batches):
        """
        Fetch a list of projects matching ``cron_batches``.

        ``cron_batches`` can be a list of cron_batch names.
        """
        return SQLDataSource.get_cron_batch_projects(cron_batches)


    @classmethod
    def get_projects_by_cron_batch(cls):
        """
        Return a dict of all the cron_batch values and which projects are in them.
        """
        return SQLDataSource.get_projects_by_cron_batch()


    def get_oauth_consumer_secret(self, key):
        ds = self.sources['objectstore'].datasource
        secret = ds.get_oauth_consumer_secret(key)
        return secret


    def get_product_test_os_map(self):

        proc = 'perftest.selects.get_product_test_os_map'

        product_tuple = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return product_tuple


    def get_operating_systems(self, key_column=None):

        operating_systems = dict()

        proc = 'perftest.selects.get_operating_systems'

        if key_column:
            operating_systems = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                key_column=key_column,
                return_type='dict',
                )
        else:
            os_tuple = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                )

            operating_systems = self._get_unique_key_dict(os_tuple,
                                                      ['name', 'version'])

        return operating_systems


    def get_tests(self, key_column='name'):

        proc = 'perftest.selects.get_tests'

        test_dict = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column=key_column,
            return_type='dict',
            )

        return test_dict


    def get_products(self, key_column=None):

        products = dict()

        proc = 'perftest.selects.get_product_data'

        if key_column:
            products = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                key_column=key_column,
                return_type='dict',
                )
        else:
            products_tuple = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                )

            products = self._get_unique_key_dict(products_tuple,
                                             ['product', 'branch', 'version'])

        return products


    def get_default_product(self):

        proc = 'perftest.selects.get_default_product'

        default_product = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple'
                )

        product_data = {}
        if default_product:
            product_data = default_product[0]

        return product_data


    def get_machines(self):

        proc = 'perftest.selects.get_machines'

        machines_dict = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='name',
            return_type='dict',
            )

        return machines_dict


    def get_options(self):

        proc = 'perftest.selects.get_options'

        options_dict = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='name',
            return_type='dict',
            )

        return options_dict


    def get_pages(self):

        proc = 'perftest.selects.get_pages'

        pages_dict = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='url',
            return_type='dict',
            )

        return pages_dict


    def get_aux_data(self):

        proc = 'perftest.selects.get_aux_data'

        aux_data_dict = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='name',
            return_type='dict',
            )

        return aux_data_dict


    def get_test_collections(self):

        proc = 'perftest.selects.get_test_collections'

        test_collection_tuple = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        test_collection = dict()
        for data in test_collection_tuple:

            if data['id'] not in test_collection:

                id = data['id']
                test_collection[ id ] = dict()
                test_collection[ id ]['name'] = data['name']
                test_collection[ id ]['description'] = data['description']
                test_collection[ id ]['data'] = []

            product_id = data['product_id']
            os_id = data['operating_system_id']

            test_collection[ id ]['data'].append(
                {'test_id':data['test_id'],
                 'name':data['name'],
                 'product_id':product_id,
                 'operating_system_id':os_id }
                 )

        return test_collection


    def get_test_collection_set(self):

        proc = 'perftest.selects.get_test_collections'

        test_collection_set = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='name',
            return_type='set'
            )

        return test_collection_set

    def get_test_reference_data(self, cache_key_str='reference_data'):

        json_data = '{}'
        cache_key = self.get_project_cache_key(cache_key_str)
        compressed_json_data = cache.get(cache_key)

        if not compressed_json_data:
            compressed_json_data = self.cache_ref_data(cache_key_str)

        json_data = zlib.decompress( compressed_json_data )

        return json_data

    def cache_ref_data(self, cache_key_str='reference_data'):
        #retrieve ref data
        ref_data = dict(
            operating_systems=self.get_operating_systems('id'),
            tests=self.get_tests('id'),
            products=self.get_products('id'),
            product_test_os_map=self.get_product_test_os_map(),
            test_collections=self.get_test_collections(),
            )

        json_data = json.dumps(ref_data)

        cache_key = self.get_project_cache_key(cache_key_str)

        #compress and cache reference data
        compressed_json_data = zlib.compress( json_data )

        cache.set(cache_key, compressed_json_data)

        return compressed_json_data

    def cache_default_project(self, cache_key_str='default_product'):

        default_project = self.get_default_product()
        cache_key = self.get_project_cache_key(cache_key_str)
        cache.set(cache_key, default_project)

    def get_test_run_summary(self,
                          start,
                          end,
                          product_ids,
                          operating_system_ids,
                          test_ids):

        col_data = {
           'b.product_id': utils.get_id_string(product_ids),

           'm.operating_system_id': utils.get_id_string(operating_system_ids),

           'tr.test_id': utils.get_id_string(test_ids)
        }

        rep = utils.build_replacement(col_data)

        proc = 'perftest.selects.get_test_run_summary'

        test_run_summary_table = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            replace=[ str(end), str(start), rep ],
            return_type='table',
            )

        return test_run_summary_table


    def get_all_test_runs(self):

        proc = 'perftest.selects.get_all_test_runs'

        test_run_summary_table = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='table',
            )

        return test_run_summary_table


    def get_test_run_values(self, test_run_id):

        proc = 'perftest.selects.get_test_run_values'

        test_run_value_table = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[ test_run_id ],
            return_type='table',
            )

        return test_run_value_table


    def get_test_run_value_summary(self, test_run_id):

        proc = 'perftest.selects.get_test_run_value_summary'

        test_run_value_table = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[ test_run_id ],
            return_type='table',
            )

        return test_run_value_table


    def get_page_values(self, test_run_id, page_id):

        proc = 'perftest.selects.get_page_values'

        page_values_table = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[ test_run_id, page_id ],
            return_type='table',
            )

        return page_values_table


    def get_summary_cache(self, item_id, item_data):

        proc = 'perftest.selects.get_summary_cache'

        cached_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[ item_id, item_data ],
            return_type='tuple',
            )

        return cached_data


    def get_all_summary_cache(self):

        proc = 'perftest.selects.get_all_summary_cache_data'

        data_iter = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            chunk_size=5,
            chunk_source="summary_cache.id",
            return_type='tuple',
            )

        return data_iter


    def set_default_product(self, id):

        proc = 'perftest.inserts.set_default_product'

        default_product = self.sources["perftest"].dhub.execute(
                proc=proc,
                placeholders=[id],
                debug_show=self.DEBUG,
                )

    def set_summary_cache(self, item_id, item_data, value):

        now_datetime = str( datetime.datetime.now() )

        placeholders = [
            item_id,
            item_data,
            value,
            now_datetime,
            value,
            now_datetime
            ]

        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_summary_cache',
            debug_show=self.DEBUG,
            placeholders=placeholders,
            executemany=False,
            )


    def set_test_collection(self, name, description):

        id = self._insert_data_and_get_id('set_test_collection',
                                          [ name,
                                            description,
                                            name ])

        return id


    def set_test_collection_map(self, test_collection_id, product_id):

        placeholders = [
            test_collection_id,
            product_id,
            ]

        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_test_collection_map',
            debug_show=self.DEBUG,
            placeholders=placeholders)


    def store_test_data(self, json_data, error=None):
        """Write the JSON to the objectstore to be queued for processing."""

        date_loaded = int( time.time() )
        error_flag = "N" if error is None else "Y"
        error_msg = error or ""

        self.sources["objectstore"].dhub.execute(
            proc='objectstore.inserts.store_json',
            placeholders=[ date_loaded, json_data, error_flag, error_msg ],
            debug_show=self.DEBUG
            )


    def retrieve_test_data(self, limit):
        """
        Retrieve JSON blobs from the objectstore.

        Does not claim rows for processing; should not be used for actually
        processing JSON blobs into perftest schema.

        Used only by the `transfer_data` management command.

        """
        proc = "objectstore.selects.get_unprocessed"
        json_blobs = self.sources["objectstore"].dhub.execute(
            proc=proc,
            placeholders=[ limit ],
            debug_show=self.DEBUG,
            return_type='tuple'
            )

        return json_blobs


    def load_test_data(self, data):
        """Load TestData instance into perftest db, return test_run_id."""

        # Get/Set reference info, all inserts use ON DUPLICATE KEY
        test_id = self._get_or_create_test_id(data)
        os_id = self._get_or_create_os_id(data)
        product_id = self._get_or_create_product_id(data)
        machine_id = self._get_or_create_machine_id(data, os_id)

        # Insert build and test_run data.
        build_id = self._set_build_data(data, product_id)
        test_run_id = self._set_test_run_data(
            data,
            test_id,
            build_id,
            machine_id
            )

        self._set_option_data(data, test_run_id)
        self._set_test_values(data, test_id, test_run_id)
        self._set_test_aux_data(data, test_id, test_run_id)

        return test_run_id


    def process_objects(self, loadlimit):
        """Processes JSON blobs from the objectstore into perftest schema."""
        rows = self.claim_objects(loadlimit)

        for row in rows:
            row_id = int(row['id'])
            try:
                data = TestData.from_json(row['json_blob'])
                test_run_id = self.load_test_data(data)
            except TestDataError as e:
                self.mark_object_error(row_id, str(e))
            except Exception as e:
                self.mark_object_error(
                    row_id,
                    u"Unknown error: {0}: {1}".format(
                        e.__class__.__name__, unicode(e))
                    )
            else:
                self.mark_object_complete(row_id, test_run_id)


    def claim_objects(self, limit):
        """
        Claim & return up to ``limit`` unprocessed blobs from the objectstore.

        Returns a tuple of dictionaries with "json_blob" and "id" keys.

        May return more than ``limit`` rows if there are existing orphaned rows
        that were claimed by an earlier connection with the same connection ID
        but never completed.

        """
        proc_mark = 'objectstore.updates.mark_loading'
        proc_get  = 'objectstore.selects.get_claimed'

        # Note: this claims rows for processing. Failure to call load_test_data
        # on this data will result in some json blobs being stuck in limbo
        # until another worker comes along with the same connection ID.
        self.sources["objectstore"].dhub.execute(
            proc=proc_mark,
            placeholders=[ limit ],
            debug_show=self.DEBUG,
            )

        # Return all JSON blobs claimed by this connection ID (could possibly
        # include orphaned rows from a previous run).
        json_blobs = self.sources["objectstore"].dhub.execute(
            proc=proc_get,
            debug_show=self.DEBUG,
            return_type='tuple'
            )

        return json_blobs


    def mark_object_complete(self, object_id, test_run_id):
        """ Call to database to mark the task completed """
        self.sources["objectstore"].dhub.execute(
            proc="objectstore.updates.mark_complete",
            placeholders=[test_run_id, object_id],
            debug_show=self.DEBUG
            )


    def mark_object_error(self, object_id, error):
        """ Call to database to mark the task completed """
        self.sources["objectstore"].dhub.execute(
            proc="objectstore.updates.mark_error",
            placeholders=[error, object_id],
            debug_show=self.DEBUG
            )


    def _set_test_aux_data(self, data, test_id, test_run_id):
        """Insert test aux data to db for given test_id and test_run_id."""
        for aux_data, aux_values in data.get('results_aux', {}).items():
            aux_data_id = self._get_or_create_aux_id(aux_data, test_id)

            placeholders = []
            for index, value in enumerate(aux_values, 1):

                string_data = ""
                numeric_data = 0
                if utils.is_number(value):
                    numeric_data = value
                else:
                    string_data = value

                placeholders.append(
                    (
                        test_run_id,
                        index,
                        aux_data_id,
                        numeric_data,
                        string_data,
                        )
                    )

            self._insert_data(
                'set_aux_values', placeholders, executemany=True)


    def _set_test_values(self, data, test_id, test_run_id):
        """Insert test values to database for given test_id and test_run_id."""
        for page, values in data['results'].items():

            page_id = self._get_or_create_page_id(page, test_id)

            placeholders = []
            for index, value in enumerate(values, 1):
                placeholders.append(
                    (
                        test_run_id,
                        index,
                        page_id,
                        # TODO: Need to get the value id into the json
                        1,
                        value,
                        )
                    )

            self._insert_data(
                'set_test_values', placeholders, executemany=True)


    def _get_or_create_aux_id(self, aux_data, test_id):
        """Given aux name and test id, return aux id, creating if needed."""
        # Insert the test id and aux data if it doesn't exist
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_aux_ref_data',
            placeholders=[
                test_id,
                aux_data,
                test_id,
                aux_data
                ],
            debug_show=self.DEBUG,
            )

        # Get the aux data id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_aux_data_id',
            placeholders=[test_id, aux_data],
            debug_show=self.DEBUG,
            return_type='iter',
            )

        return id_iter.get_column_data('id')


    def _get_or_create_page_id(self, page, test_id):
        """Given page name and test id, return page id, creating if needed."""
        # Insert the test id and page name if it doesn't exist
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_pages_ref_data',
            placeholders=[
                test_id,
                page,
                test_id,
                page
                ],
            debug_show=self.DEBUG,
            )

        # Get the page id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_page_id',
            placeholders=[test_id, page],
            debug_show=self.DEBUG,
            return_type='iter',
            )

        return id_iter.get_column_data('id')


    def _set_option_data(self, data, test_run_id):
        """Insert option data for given test run id."""

        testrun = data['testrun']

        placeholders = []
        for option, value in testrun.get('options', {}).items():

            """
            TODO: Add handling for inserting extensions in
             a separate table.  Until we have handling, ignore
             the extensions option to avoid generating a data
             truncation error. An extension value will look like:

             [ { "name":"extension_name1" },
              { "name":"exension_name2" } ...etc ]

             Reference: https://bugzilla.mozilla.org/show_bug.cgi?id=769479
            """
            if option == 'extensions':
                continue

            option_id = self._get_or_create_option_id(option)

            placeholders.append([test_run_id, option_id, value])

        self._insert_data(
            'set_test_option_values', placeholders, executemany=True)


    def _set_build_data(self, data, product_id):
        """Inserts build data into the db and returns build ID."""
        machine = data['test_machine']
        build = data['test_build']

        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_build_data',
            placeholders=[
                product_id,
                build['id'],
                machine['platform'],
                build['revision'],
                # TODO: Need to get the build type into the json
                'opt',
                # TODO: need to get the build date into the json
                int(time.time()),
                build['id']
                ],
            debug_show=self.DEBUG
            )

        # Get the build id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_build_id',
            placeholders=[build['id']],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _set_test_run_data(self, data, test_id, build_id, machine_id):
        """Inserts testrun data into the db and returns test_run id."""

        try:
            run_date = int(data['testrun']['date'])
        except ValueError:
            raise TestDataError(
                "Bad value: ['testrun']['date'] is not an integer.")

        test_run_id = self._insert_data_and_get_id(
            'set_test_run_data',
            [
                test_id,
                build_id,
                machine_id,
                # denormalization; avoid join to build table to get revision
                data['test_build']['revision'],
                run_date,
                ]
            )

        return test_run_id


    def _insert_data(self, statement, placeholders, executemany=False):
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.' + statement,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            executemany=executemany,
            )


    def _insert_data_and_get_id(self, statement, placeholders):
        """Execute given insert statement, returning inserted ID."""
        self._insert_data(statement, placeholders)
        return self._get_last_insert_id()


    def _get_last_insert_id(self, source="perftest"):
        """Return last-inserted ID."""
        return self.sources[source].dhub.execute(
            proc='generic.selects.get_last_insert_id',
            debug_show=self.DEBUG,
            return_type='iter',
            ).get_column_data('id')


    def _get_or_create_machine_id(self, data, os_id):
        """
        Given a TestData instance, returns the test id from the db.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        machine = data['test_machine']

        # Insert the the machine name and timestamp if it doesn't exist
        date_added = int(time.time())
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_machine_ref_data',
            placeholders=[
                machine['name'],
                os_id,
                date_added,
                machine['name'],
                os_id
                ],

            debug_show=self.DEBUG)

        # Get the machine id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_machine_id',
            placeholders=[machine['name'], os_id],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_test_id(self, data):
        """
        Given a TestData instance, returns the test id from the db.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        testrun = data['testrun']

        try:
            # TODO: version should be required; currently defaults to 1
            version = int(testrun.get('suite_version', 1))
        except ValueError:
            raise TestDataError(
                "Bad value: ['testrun']['suite_version'] is not an integer.")

        # Insert the test name and version if it doesn't exist
        self.sources['perftest'].dhub.execute(
            proc='perftest.inserts.set_test_ref_data',
            placeholders=[
                testrun['suite'],
                version,
                testrun['suite'],
                version
                ],
            debug_show=self.DEBUG
            )

        # Get the test name id
        id_iter = self.sources['perftest'].dhub.execute(
            proc='perftest.selects.get_test_id',
            placeholders=[testrun['suite'], version],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_os_id(self, data):
        """
        Given a full test-data structure, returns the OS id from the database.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        machine = data['test_machine']
        os_name = machine['os']
        os_version = machine['osversion']

        # Insert the operating system name and version if it doesn't exist
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_os_ref_data',
            placeholders=[
                os_name,
                os_version,
                os_name,
                os_version
                ],
            debug_show=self.DEBUG)

        # Get the operating system name id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_os_id',
            placeholders=[os_name, os_version],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_option_id(self, option):
        """Return option id for given option name, creating it if needed."""
        # Insert the option name if it doesn't exist
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_option_ref_data',
            placeholders=[ option, option],
            debug_show=self.DEBUG)

        # Get the option id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_option_id',
            placeholders=[ option ],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_product_id(self, data):
        """Return product id for given TestData, creating product if needed."""
        build = data['test_build']

        product = build['name']
        branch = build['branch']
        version = build['version']

        # Insert the product, branch, and version if it doesn't exist
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_product_ref_data',
            placeholders=[
                product,
                branch,
                version,
                product,
                branch,
                version
                ],
            debug_show=self.DEBUG)

        # Get the product id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_product_id',
            placeholders=[ product, branch, version ],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_unique_key_dict(self, data_tuple, key_strings):

        data_dict = dict()
        for data in data_tuple:
            unique_key = ""
            for key in key_strings:
                unique_key += str(data[key])
            data_dict[ unique_key ] = data['id']
        return data_dict


class MetricsTestModel(DatazillaModelBase):
    """
    Public interface to all data access for the metrics part of the perftest
    schema.
    """

    # Content types that every project will have
    CONTENT_TYPES = ["perftest"]

    ###
    # Metric keys are used together to define a unique Metrics Datum
    #
    # Metrics Datum: A target for a metrics method made up of a single set
    # of test value replicates.
    #
    # Example: ttest applied to all the replicates associated with a given
    # test suite page.
    ###
    METRIC_KEYS = [
        'product_id',
        'operating_system_id',
        'processor',
        'test_id',
        'page_id'
        ]

    ###
    # Metric summary keys are used together to define a unique Metric
    # Summary Datum
    #
    # Metric Summary Datum: A target for a metrics method made up of
    # a single set of values computed by a metrics method.
    #
    # Example: fdr applied to all of the p values computed
    # in a ttest.
    ###
    METRIC_SUMMARY_KEYS = [
        'product_id',
        'operating_system_id',
        'processor',
        'test_id'
        ]

    KEY_DELIMITER = '__'

    #Number of characters in a node that are
    #used in the revision string
    REVISION_CHAR_COUNT = 12

    def __init__(self, project=None, metrics=()):
        super(MetricsTestModel, self).__init__(project)
        self.skip_revisions = set()

        self.metrics = metrics or self._get_metric_collection()

        self.mf = MetricsMethodFactory(self.metrics)

    @classmethod
    def get_metrics_key(cls, data):
        return cls.KEY_DELIMITER.join(
            map(lambda s: str( data[s] ), cls.METRIC_KEYS)
            )

    @classmethod
    def get_metrics_summary_key(cls, data):
        return cls.KEY_DELIMITER.join(
            map(lambda s: str( data[s] ), cls.METRIC_SUMMARY_KEYS)
            )

    @classmethod
    def extend_with_metrics_keys(cls, data, add_keys=[]):
        keys = []
        keys.extend(cls.METRIC_KEYS)
        if add_keys:
            keys.extend(add_keys)
        return dict([(k, data.get(k, None)) for k in keys])

    @classmethod
    def get_revision_from_node(cls, node):
        return node[0:cls.REVISION_CHAR_COUNT]

    def add_skip_revision(self, revision):
        if revision:
            self.skip_revisions.add(revision)

    def get_metric_summary_name(self, test_name):
        m = self.mf.get_metric_method(test_name)
        return m.SUMMARY_NAME

    def get_test_values(self, revision, struct_type='metric_key_lookup'):
        """
        Retrieve all test values associated with a givec revision.

        revision - revision/changeset string.

        struct_type - Determines the structure of the data returned.
            Possible values are: metric_summary_lookup, metric_key_lookup,
            metric_data_lookup.  See adapt_data for detailed data structure
            descriptions.
        """

        proc = 'perftest.selects.get_test_values'

        revision_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[revision],
            return_type='tuple',
            )

        return self.adapt_data(struct_type, revision_data)

    def get_threshold_data(self, ref_data):
        """
        Retrieve all metric threshold data for a given metric key found
        in the supplied dictionary ref_data.

        ref_data - Dictionary containing all METRIC_KEYS and their
            associated values.

        struct_type - Determines the structure of the data returned.
            Possible values are: metric_summary_lookup, metric_key_lookup,
            metric_data_lookup.  See adapt_data for detailed data structure
            descriptions.
        """

        m = self.mf.get_metric_method(ref_data['test_name'])
        metric_id = m.get_metric_id()

        proc = 'perftest.selects.get_metric_threshold'

        placeholders = [
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['page_id']
            ]

        threshold_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            return_type='tuple',
            )

        return self.adapt_data('threshold_data_lookup', threshold_data)

    def get_metrics_data(self, revision):
        """
        Retrieve all metrics data associated with a given revision.
        """

        proc = 'perftest.selects.get_computed_metrics'

        computed_metrics = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[revision],
            return_type='tuple'
            )

        return self.adapt_data(
            'metric_data_lookup', computed_metrics
            )

    def get_parent_test_data(
        self, pushlog, index, child_key, metric_method_data=None
        ):
        """
        Walks back through the branch 'pushlog' starting at the 'index'
        position before the child, looking for the parent push of
        the metrics datum specified by 'child_key'.

        pushlog - Pushlog data structure for a given branch (generated by
            PushLogModel.get_branch_pushlog.

        index - Pushlog index where the child is found.

        child_key - Metrics datum key of the child to find a parent for.

        metric_method_data - Data for the metric method to use to validate
            metric test results.  If it's provided a parent must pass the
            MetricMethod.evaluate_metric_result test to be considered a
            viable parent.
        """

        parent_data = {}
        test_result = {}
        parent_index = index

        try:

            while not parent_data:

                if parent_index == 0:
                    break
                else:
                    #walk back through the pushlog to find the parent
                    parent_index -= 1

                parent_node = pushlog[ parent_index ]
                revision = self.get_revision_from_node(parent_node['node'])

                #skip pushes without data
                if revision in self.skip_revisions:
                    continue

                data = self.get_test_values(revision)

                #no data for this revision, skip
                if not data:
                    self.add_skip_revision(revision)
                    continue

                if child_key in data:
                    if metric_method_data:
                        m = self.mf.get_metric_method(
                            data[child_key]['ref_data']['test_name']
                            )

                        test_result = m.run_metric_method(
                            metric_method_data,
                            data[child_key]['values']
                            )

                        #Confirm that it passes test
                        if m.evaluate_metric_result(test_result):
                            #parent found that passes metric test
                            #requirements
                            parent_data = data[child_key]
                    else:
                        #parent found
                        parent_data = data[child_key]

        except IndexError:
            #last index reached, no parent with data found,
            #return empty data structures
            return parent_data, test_result

        else:
            #parent with data found
            return parent_data, test_result

    def run_metric_method(self, ref_data, child_data, parent_data):

        m = self.mf.get_metric_method(ref_data['test_name'])
        results = m.run_metric_method(child_data, parent_data)
        return results

    def run_metric_summary(self, ref_data, data):

        m = self.mf.get_metric_method(ref_data['test_name'])
        results = m.run_metric_summary(data)
        return results

    def store_metric_results(
        self, revision, ref_data, results,
        revision_pushlog_date, threshold_pushlog_date
        ):

        proc = 'perftest.inserts.set_test_page_metric'

        m = self.mf.get_metric_method(ref_data['test_name'])
        placeholders = m.get_data_for_metric_storage(ref_data, results)

        if placeholders:

            self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )

            if m.evaluate_metric_result(results):
                if threshold_pushlog_date:
                    #####
                    # Don't update the threshold metric if the pushlog date
                    # associated with this revision is from the past.
                    ####
                    if int(revision_pushlog_date) >= \
                        (threshold_pushlog_date):

                        self.insert_or_update_metric_threshold(
                            revision,
                            ref_data,
                            m.get_metric_id(),
                            revision_pushlog_date
                            )
                else:
                    ####
                    # If no threshold pushlog date is provided this is an
                    # insert, the data was derived from a direct comparison
                    # with a pushlog parent.
                    ####
                    self.insert_or_update_metric_threshold(
                        revision,
                        ref_data,
                        m.get_metric_id(),
                        revision_pushlog_date
                        )

    def store_metric_summary_results(self, revision, ref_data, results):

        proc = 'perftest.inserts.set_test_page_metric'

        m = self.mf.get_metric_method(ref_data['test_name'])

        placeholders = m.get_data_for_summary_storage(ref_data, results)
        if placeholders:

            self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )

    def insert_or_update_metric_threshold(
        self, revision, ref_data, metric_id, push_date
        ):

        proc = 'perftest.inserts.set_metric_threshold'

        placeholders = [

            ##Insert Placeholders
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['test_run_id'],
            revision,
            push_date,

            ##Duplicate Key Placeholders
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['test_run_id'],
            revision,
            push_date
            ]

        self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=settings.DEBUG,
            placeholders=placeholders
            )

    def adapt_data(self, struct_type, data):

        adapted_data = {}
        if struct_type == 'metric_summary_lookup':
            adapted_data = self._get_metric_summary_key_lookup(data)
        elif struct_type == 'metric_key_lookup':
            adapted_data = self._get_metric_key_lookup(data)
        elif struct_type == 'threshold_data_lookup':
            adapted_data = self._get_threshold_data_lookup(data)
        elif struct_type == 'metric_data_lookup':
            adapted_data = self._get_metric_data_lookup(data)
        else:
            adapted_data = self._get_metric_key_lookup(data)

        return adapted_data

    def _get_metric_data_lookup(self, data):
        """
        Converts datasource tuple to

        metric_key : {
            { ref_data: {
                all self.METRIC_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision
                }
            },

           { values : [ {
                value:test value,
                page_id:page_id,
                metric_value_id:metric_value_id,
                metric_value_name:metric_value_name
                }, ...
             ]
           }
        }
        """

        key_lookup = {}
        for d in data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision']
                        )
                    }
            key_lookup[key]['values'].append( {
                'value':d['value'],
                'page_id':d['page_id'],
                'metric_value_id':d['metric_value_id'],
                'metric_value_name':d['metric_value_name']
                } )

        return key_lookup

    def _get_threshold_data_lookup(self, data):
        """
        Converts datasource tuple to

        metric_key : {
            { ref_data: {
                all self.METRIC_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision,
                push_date: int representing time associated with the push
                           this datum came from.
                }
            },

           { values : [ test_value1, test_value2, test_value3, ... ] }
        }
        """

        key_lookup = {}
        for d in data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name',
                            'revision', 'push_date']
                        )
                    }

            key_lookup[key]['values'].append( d['value'] )

        return key_lookup

    def _get_metric_key_lookup(self, data):
        """
        Converts datasource tuple to

        metric_key : {
            { ref_data: {
                all self.METRIC_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision
                }
            },

           { values : [ test_value1, test_value2, test_value3, ... ] }
        }
        """

        key_lookup = {}
        for d in data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision']
                        )
                    }
            key_lookup[key]['values'].append( d['value'] )

        return key_lookup

    def _get_metric_summary_key_lookup(self, data):
        """
        Converts datasource tuple to

        metric_summary_key : {
            { ref_data: {
                all self.METRIC_SUMMARY_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision
                }
            },

           { values : [ {
                dict containing all key/value pairs from the
                SELECT
                }, ...
             ]
           }
        }
        """

        test_lookup = {}
        for d in data:
            key = self.get_metrics_summary_key(data)
            if key not in test_lookup:
                #set reference data
                test_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision']
                        )
                    }
            test_lookup[key]['values'].append(d)

        return test_lookup

    def _get_metric_collection(self):
        proc = 'perftest.selects.get_metric_collection'

        metric_collection = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='metric_name',
            return_type='tuple',
            )
        return metric_collection


class TestDataError(ValueError):
    pass


class TestData(dict):
    """
    Encapsulates data access from incoming test data structure.

    All missing-data errors raise ``TestDataError`` with a useful
    message. Unlike regular nested dictionaries, ``TestData`` keeps track of
    context, so errors contain not only the name of the immediately-missing
    key, but the full parent-key context as well.

    """
    def __init__(self, data, context=None):
        """Initialize ``TestData`` with a data dict and a context list."""
        self.context = context or []
        super(TestData, self).__init__(data)


    @classmethod
    def from_json(cls, json_blob):
        """Create ``TestData`` from a JSON string."""
        try:
            data = json.loads(json_blob)
        except ValueError as e:
            raise TestDataError("Malformed JSON: {0}".format(e))

        return cls(data)


    def __getitem__(self, name):
        """Get a data value, raising ``TestDataError`` if missing."""
        full_context = list(self.context) + [name]

        try:
            value = super(TestData, self).__getitem__(name)
        except KeyError:
            raise TestDataError("Missing data: {0}.".format(
                    "".join(["['{0}']".format(c) for c in full_context])))

        # Provide the same behavior recursively to nested dictionaries.
        if isinstance(value, dict):
            value = self.__class__(value, full_context)

        return value
