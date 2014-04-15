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
import socket
import zlib
import MySQLdb

from collections import defaultdict

from warnings import filterwarnings, resetwarnings

from django.conf import settings
from django.core.cache import cache


from . import utils
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

        data = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data


    def get_branch_list(self, branch=None):
        # if a branch was specified, limit the list to only that branch
        # TODO: make a separate select for this case, instead of all
        branch_list = self.get_all_branches()
        if branch:
            branch_list=[x for x in branch_list if x["name"] == branch or x["alt_name"] == branch]
            if len(branch_list) < 1:
                self.println("Branch not found: {0}".format(branch))
                return

        return branch_list

    def get_branch_uri(self, branch=None):

        data = []

        if branch:

            proc = 'hgmozilla.selects.get_branch_uri'

            data = self.hg_ds.dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                placeholders=[branch, branch],
                return_type='tuple',
                )
        else:
            proc = 'hgmozilla.selects.get_all_branch_uris'

            data = self.hg_ds.dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                )

        return data

    def get_all_pushlogs(self):

        proc = 'hgmozilla.selects.get_all_pushlogs'

        data = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data


    def get_all_changesets(self):

        proc = 'hgmozilla.selects.get_all_changesets'

        data = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            )

        return data

    def get_changesets(self, pushlog_id):

        placeholders = [pushlog_id]
        proc = 'hgmozilla.selects.get_changesets'

        data = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=placeholders,
            )

        return data

    def get_branch_pushlog(
        self, branch_id, days_ago=None, numdays=None, branch_name=None
        ):
        """
        Retrieve pushes for a given branch for time range. If no
        time range is provided return all pushlogs for the branch.
        """

        data = {}

        replace = ""
        placeholders = []

        if branch_id:
            replace = " b.id=%s "
            placeholders.append(branch_id)
        elif branch_name:
            replace = " b.name=%s "
            placeholders.append(branch_name)

        if days_ago and numdays:

            day_range = utils.get_day_range(days_ago, numdays)

            placeholders.append( day_range['start'] )
            placeholders.append( day_range['stop'] )

            proc = 'hgmozilla.selects.get_branch_pushlog'

            data = self.hg_ds.dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                replace=[replace],
                placeholders=placeholders
            )

        else:
            proc = 'hgmozilla.selects.get_all_branch_pushlogs'

            data = self.hg_ds.dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                replace=[replace],
                placeholders=placeholders
            )

        return data

    def get_branch_pushlog_by_revision(
        self, revision, branch_name, pushes_before, pushes_after
        ):

        #Get the push id for this revision
        push_id_proc = 'hgmozilla.selects.get_push_id_from_revision'

        push_data = self.hg_ds.dhub.execute(
            proc=push_id_proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=[revision, branch_name, branch_name]
            )

        if not push_data:
            return push_data

        node = push_data[0]['node']
        push_id = push_data[0]['push_id']
        branch_id = push_data[0]['branch_id']

        pushes_before_proc = 'hgmozilla.selects.get_push_ids_before_node'
        pushes_after_proc = 'hgmozilla.selects.get_push_ids_after_node'

        before_boundary = push_id - pushes_before

        pushes_before_data = self.hg_ds.dhub.execute(
            proc=pushes_before_proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=[ push_id, before_boundary, branch_id ]
            )

        after_boundary = push_id + pushes_after

        pushes_after_data = self.hg_ds.dhub.execute(
            proc=pushes_after_proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=[ push_id, after_boundary, branch_id ]
            )

        del push_data[0]['branch_id']
        del push_data[0]['node']

        #Combine all of the requested push data
        pushlog = pushes_before_data + push_data + pushes_after_data

        #Retrieve a complete list of all of the pushlog ids
        pushlog_ids = []

        map(
            lambda n: pushlog_ids.append(n['pushlog_id']),
            pushlog
            )

        #Use a separate query to retrieve associated revisions so
        #we can control the number of pushes by using a LIMIT clause
        changeset_data_proc = 'hgmozilla.selects.get_changeset_data_for_pushes'

        #Build the sql WHERE IN clause
        where_in_clause = ','.join( map( lambda v:'%s', pushlog_ids ) )

        changeset_data = self.hg_ds.dhub.execute(
            proc=changeset_data_proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=pushlog_ids,
            replace=[where_in_clause]
            )

        #Aggregate changesets
        changeset_lookup = {}
        for changeset in changeset_data:
            if changeset['pushlog_id'] not in changeset_lookup:
                changeset_struct = {
                    'revisions':[],
                    'pushlog_id':changeset['pushlog_id']
                    }

                changeset_lookup[ changeset['pushlog_id'] ] = changeset_struct

            changeset_lookup[ changeset['pushlog_id'] ]['revisions'].append(
                { 'revision':changeset['node'],
                  'desc':changeset['desc'],
                  'author':changeset['author'] }
                )

        return pushlog, changeset_lookup

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


    def store_pushlogs(
        self, repo_host, numdays, hours=None, enddate=None, branch=None
        ):
        """
        Main entry point to store pushlogs for branches.

        If branch is None, then store pushlogs for ALL branches that we
        know about.

        If enddate is None, then use today as the enddate.

        """

        ###
        #This sets the socket timeout globally for all socket operations.
        #Its default setting is None.  In production, the /json-pushes
        #web service call will occasionally hang on a TCP CLOSE_WAIT state.
        ###
        socket.setdefaulttimeout(120)

        # fetch the list of known branches.
        branch_list = self.get_branch_list(branch)

        # parameters sent to the requests for pushlog data
        params = {}
        if numdays:
            params = self.get_params(numdays, enddate)

        if hours:
            params = {
                "full": 1,
                "maxhours": hours,
                }

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

            json_data = ''

            try:
                res = urllib.urlopen(url)
                json_data = res.read()

            except socket.timeout:
                continue

            try:
                pushlog_dict = json.loads(json_data)
                self._insert_branch_pushlogs(br["id"], pushlog_dict)
                self.branch_count += 1

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

    def get_node_from_revision(self, revision, branch):

        proc = 'hgmozilla.selects.get_node_from_revision'

        data = self.hg_ds.dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=[revision, branch, branch]
            )

        node = {}
        if data:
            node = data[0]

        return node

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

            except MySQLdb.IntegrityError as e:
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

            except MySQLdb.IntegrityError:
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

    # Total number of replicates allowed for a
    # single test suite associated with a JSON object
    REPLICATE_LIMIT = 5000

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

    def get_revision_products(self, revision, branch):

        proc = 'perftest.selects.get_revision_products'

        products = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            return_type='tuple',
            placeholders=[revision]
            )

        return products


    def get_default_products(self):

        proc = 'perftest.selects.get_default_products'

        products = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple'
                )

        default_products = ','.join(
            [ str(d['id']) for d in products ]
            )

        return default_products

    def get_default_branch_version(self, branch, product_name):

        proc = 'perftest.selects.get_default_products'

        products = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple'
                )

        target_product = {}

        for product in products:
            if (product['branch'] == branch) and (product['product'] == product_name):
                target_product = product
                break

        return target_product

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

        pages_tuple = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            )

        pages_dict = {}
        for page_data in pages_tuple:
            if page_data['url'] not in pages_dict:
                pages_dict[ page_data['url'] ] = {}
                pages_dict[ page_data['url'] ]['test_ids'] = {}
                pages_dict[ page_data['url'] ]['id'] = page_data['id']
                pages_dict[ page_data['url'] ]['url'] = page_data['url']

            pages_dict[ page_data['url'] ]['test_ids'][ page_data['test_id'] ] = True

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

        default_project = self.get_default_products()
        cache_key = self.get_project_cache_key(cache_key_str)
        cache.set(cache_key, default_project)



    def get_test_run_ids(
        self, branch, revisions, product_name=None, os_name=None,
        os_version=None, branch_version=None, processor=None,
        build_type=None, test_name=None, page_name=None):

        proc = 'perftest.selects.get_test_run_ids'
        placeholders = [branch]
        rep = []

        if revisions:
            revision_string = ','.join( map( lambda v:str(v), revisions ) )
            self.get_replace_and_placeholders(
                rep, placeholders, 'tr.revision', revision_string
                )
        if product_name:
            self.get_replace_and_placeholders(
                rep, placeholders, 'p.product', product_name
                )
        if os_name:
            self.get_replace_and_placeholders(
                rep, placeholders, 'os.name', os_name
                )
        if os_version:
            self.get_replace_and_placeholders(
                rep, placeholders, 'os.version', os_version
                )
        if branch_version:
            self.get_replace_and_placeholders(
                rep, placeholders, 'p.version', branch_version
                )
        if processor:
            self.get_replace_and_placeholders(
                rep, placeholders, 'b.processor', processor
                )
        if build_type:
            self.get_replace_and_placeholders(
                rep, placeholders, 'b.build_type', build_type
                )
        if test_name:
            self.get_replace_and_placeholders(
                rep, placeholders, 't.name', test_name
                )

        replace = [" ".join(rep)] if len(rep) else [" "]

        id_list = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            replace=replace,
            )

        test_run_ids = [ d['test_run_id'] for d in id_list ]

        return test_run_ids

    def get_replace_and_placeholders(
        self, replace, placeholders, col_name, value
        ):
        """
        Build dynamic sql WHERE IN clause with parameterized values
        """

        #clean up leading/ending whitspace
        values = map(lambda v:v.strip(), value.split(','))

        #add the values to list of placeholders
        placeholders.extend(values)

        #build the sql WHERE IN clause
        where_in_clause = ','.join( map( lambda v:'%s', values ) )

        #add the dynamic sql to the replace list
        replace.append(
            " AND {0} IN ({1})".format(col_name, where_in_clause)
            )

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

        data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            chunk_size=5,
            chunk_source="summary_cache.id",
            return_type='tuple',
            )

        return data

    def get_last_test_run_date(self, machine, product, branch, version, tests,
        pages):

        proc = 'perftest.selects.get_last_test_run_date'

        tests_string = '(' + ','.join('"{0}"'.format(s) for s in tests) + ')'
        pages_string = '(' + ','.join('"{0}"'.format(s) for s in pages) + ')'

        data = self.sources["perftest"].dhub.execute(
            proc = proc,
            debug_show = self.DEBUG,
            placeholders = [ machine, product, branch, version ],
            replace = [ tests_string, pages_string ]
        )

        return data

    def get_canonical_value(self, table, column, value):

        proc = "perftest.selects.get_canonical_value"

        data = self.sources["perftest"].dhub.execute(
            proc = proc,
            debug_show = self.DEBUG,
            placeholders = [ value ],
            replace = [ table, column ]
        )

        return data[0][column] if data else None

    def set_default_product(self, id, value):

        proc = 'perftest.inserts.set_default_product'

        default_product = self.sources["perftest"].dhub.execute(
                proc=proc,
                placeholders=[value, id],
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

        # NOTE: Disabling warnings here.  A warning is generated in the
        # production environment that is specific to the master/slave
        # configuration.
        filterwarnings('ignore', category=MySQLdb.Warning)

        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_summary_cache',
            debug_show=self.DEBUG,
            placeholders=placeholders,
            executemany=False,
            )

        resetwarnings()

    def set_test_collection(self, name, description):

        id = self._insert_data_and_get_id('set_test_collection',
                                          [ name,
                                            description ])

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

        date_loaded = utils.get_now_timestamp()
        error_flag = "N" if error is None else "Y"
        error_msg = error or ""

        self.sources["objectstore"].dhub.execute(
            proc='objectstore.inserts.store_json',
            placeholders=[ date_loaded, json_data, error_flag, error_msg ],
            debug_show=self.DEBUG
            )

        return self._get_last_insert_id(source='objectstore')

    def pre_process_data(self, unquoted_json_data, deserialized_json):
        """Carry out project specific pre-processing of JSON objects."""

        #If it's malformed json this will not be defined
        if deserialized_json:

            if (self.project == 'talos') and \
               ('tp5' in deserialized_json['testrun']['suite']):

                new_key = 'talos_aux'

                results_aux = deserialized_json.get('results_aux', {})

                if results_aux:
                    #Insure that auxilliary data is not indexed
                    #for tp5*. The auxilliary data should be placed
                    #in a top level key that is not indexed.
                    deserialized_json[new_key] = results_aux

                    del deserialized_json['results_aux']

                    unquoted_json_data = json.dumps(deserialized_json)

        return unquoted_json_data

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

        # Apply all platform specific hacks to account for mozilla
        # production test environment problems
        self._adapt_production_data(data)

        # Get/Set reference info, all inserts use ON DUPLICATE KEY
        test_id = self._get_or_create_test_id(data)
        os_id = self._get_or_create_os_id(data)
        product_id = self._get_or_create_product_id(data)
        machine_id = self._get_or_create_machine_id(data, os_id)

        # Insert build and test_run data.
        build_id = self._get_or_create_build_id(data, product_id)

        test_run_id = self._set_test_run_data(
            data,
            test_id,
            build_id,
            machine_id
            )

        self._set_option_data(data, test_run_id)
        self._set_test_values(data, test_id, test_run_id)
        self._set_test_aux_data(data, test_id, test_run_id)

        # Make project specific changes
        self._adapt_project_specific_data(data, test_run_id, machine_id)

        return test_run_id


    def process_objects(self, loadlimit):
        """Processes JSON blobs from the objectstore into perftest schema."""
        rows = self.claim_objects(loadlimit)
        test_run_ids_loaded = []

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
                test_run_ids_loaded.append(test_run_id)

        return test_run_ids_loaded

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

        # Note: There is a bug in MySQL http://bugs.mysql.com/bug.php?id=42415
        # that causes the following warning to be generated in the production
        # environment:
        #
        # _mysql_exceptions.Warning: Unsafe statement written to the binary
        # log using statement format since BINLOG_FORMAT = STATEMENT. The
        # statement is unsafe because it uses a LIMIT clause. This is
        # unsafe because the set of rows included cannot be predicted.
        #
        # I have been unable to generate the warning in the development
        # environment because the warning is specific to the master/slave
        # replication environment which only exists in production.In the
        # production environment the generation of this warning is causing
        # the program to exit.
        #
        # The mark_loading SQL statement does execute an UPDATE/LIMIT but now
        # implements an "ORDER BY id" clause making the UPDATE
        # deterministic/safe.  I've been unsuccessfull capturing the specific
        # warning generated without redirecting program flow control.  To
        # ressolve the problem in production, we're disabling MySQLdb.Warnings
        # before executing mark_loading and then re-enabling warnings
        # immediately after.  If this bug is ever fixed in mysql this handling
        # should be removed. Holy Hackery! -Jeads
        filterwarnings('ignore', category=MySQLdb.Warning)

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

        resetwarnings()

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

    def get_b2g_value_summary_by_test_ids(
        self, branch, device, test_ids, url, begin_date, end_date
        ):
        #####
        #TODO: This needs to be moved to a derived class
        #####

        data = []

        if branch and test_ids and url and begin_date and end_date:

            proc = 'perftest.selects.get_b2g_value_summary_by_test_id'

            r_string = ','.join( map( lambda t_id: '%s', test_ids ) )

            test_ids.append( branch )
            test_ids.append( device )
            test_ids.append( url )
            test_ids.append( begin_date )
            test_ids.append( end_date )

            data = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                placeholders=test_ids,
                replace=[ r_string ]
                )

            for index, row in enumerate(data):

                median = self._get_median_from_sorted_list(
                    # convert string containing comma delimited list of
                    # values to a list of integers
                    map( lambda x:float(x or 0), row['replicates'].split(',') )
                    )

                data[index]['median'] = median

                # remove list of replicates before returning
                del data[index]['replicates']

        return data

    def get_test_run_ids_by_revisions(
        self, branch, revision, gecko_revision, test_id, test_type):
        #TODO: This method is specific to the b2g project and should
        #       be placed in a derived class
        #
        #NOTE: test_type corresponds to pages.url, b2g overloads the schema
        #       in the following way.  The test table holds applications and
        #       the pages table holds tests

        proc = 'perftest.selects.get_test_run_ids_from_revisions'

        data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[
                revision, gecko_revision, branch, test_id, test_type
                ]
            )

        test_run_ids = []
        for d in data:
            test_run_ids.append(d['id'])

        return test_run_ids

    def cycle_data(self, sql_targets={}):

        # Compute 6 month old timestamp
        min_date = int(time.time() - 15552000)

        data = self.sources['perftest'].dhub.execute(
            proc='perftest.selects.get_test_run_rows_to_cycle',
            placeholders=[min_date],
            debug_show=self.DEBUG
            )

        test_run_ids = map(lambda x:x['id'], data)

        where_in_clause = [ ','.join( map( lambda v:'%s', test_run_ids ) ) ]

        if len(test_run_ids) == 0:
            sql_targets['total_count'] = 0
            return sql_targets

        objectstore_sql_to_execute = [
            { 'sql':'objectstore.deletes.cycle_objectstore_by_test_run_ids',
              'placeholders':test_run_ids,
              'replace':where_in_clause }
            ]

        perftest_sql_to_execute = [
            { 'sql':'perftest.deletes.cycle_test_aux_data',
              'placeholders':test_run_ids,
              'replace':where_in_clause },

            { 'sql':'perftest.deletes.cycle_test_option_values',
              'placeholders':test_run_ids,
              'replace':where_in_clause },

            { 'sql':'perftest.deletes.cycle_test_value',
              'placeholders':test_run_ids,
              'replace':where_in_clause },

            { 'sql':'perftest.deletes.cycle_test_data_all_dimensions',
              'placeholders':test_run_ids,
              'replace':where_in_clause },

            { 'sql':'perftest.deletes.cycle_test_run',
              'placeholders':test_run_ids,
              'replace':where_in_clause }
            ]

        sql_targets['total_count'] = 0

        # remove data from specified objectstore and perftest tables that is
        # older than 6 months
        self._execute_table_deletes(
            min_date, 'objectstore', objectstore_sql_to_execute, sql_targets
            )

        self._execute_table_deletes(
            min_date, 'perftest', perftest_sql_to_execute, sql_targets
            )

        return sql_targets

    def _execute_table_deletes(self, min_date, source, sql_to_execute, sql_targets):

        for sql_obj in sql_to_execute:

            sql = sql_obj['sql']
            placeholders = sql_obj['placeholders']
            replace = sql_obj['replace']

            if sql not in sql_targets:
                sql_targets[sql] = None

            if (sql_targets[sql] == None) or (sql_targets[sql] > 0):

                self.sources[source].dhub.execute(
                    proc=sql,
                    placeholders=placeholders,
                    replace=replace,
                    debug_show=self.DEBUG
                    )

                row_count = self.sources[source].dhub.connection['master_host']['cursor'].rowcount

                self.sources[source].dhub.commit('master_host')

                sql_targets[sql] = row_count
                sql_targets['total_count'] += row_count

                # Allow some time for other queries to get through
                time.sleep(5)

    def _adapt_production_data(self, data):

        ###
        #In production all "mac os x" data is -Non-PGO but this is not
        #reflected in the branch name.  This is due to inconsistancies
        #in buildbot.  To account for this we append -Non-PGO to the
        #branch name for all branches for "mac os x".
        ###
        if self.project == 'talos':

            os = data['test_machine']['os'].lower()
            osversion = data['test_machine']['osversion'].lower()

            if ('mac' in os) and ('os x' in osversion):
                data['test_build']['branch'] += '-Non-PGO'

            #REMOVE AFTER BACKFILL: Insure that we don't load results_aux
            # for tp5 data in the backfill
            if 'tp5' in data['testrun']['suite']:

                new_key = 'talos_aux'

                results_aux = data.get('results_aux', {})

                if results_aux:
                    #Insure that auxilliary data is not indexed
                    #for tp5*. The auxilliary data should be placed
                    #in a top level key that is not indexed.
                    data[new_key] = results_aux
                    del data['results_aux']

    def _adapt_project_specific_data(self, data, test_run_id, machine_id):

        ###
        #TODO: This should be moved into a derived class
        ###
        if self.project == 'b2g' or self.project == 'b2gtw':
            ###
            #b2g has two unique test run fields, gecko_revision and
            #build_revision, they need to be loaded here
            ###
            self._update_b2g_test_run(data, test_run_id)
            self._update_b2g_machine_type(data, machine_id)


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

        total_replicates = 0

        for page, values in data['results'].items():

            page_id = self._get_or_create_page_id(page, test_id)

            placeholders = []
            for index, value in enumerate(values, 1):

                total_replicates += 1

                if total_replicates <= self.REPLICATE_LIMIT:

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

                else:
                    #Replicate limit reached
                    break

            if placeholders:
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


    def _get_or_create_build_id(self, data, product_id):
        """Inserts build data into the db or if the build already exists
           it returns the build id."""
        machine = data['test_machine']
        build = data['test_build']

        build_type = 'opt'

        placeholders=[
            product_id,
            build['id'],
            machine['platform'],
            build['revision'],
            # TODO: Need to get the build type into the json
            build_type,
            # TODO: need to get the build date into the json
            utils.get_now_timestamp(),

            #These params confirm identity in a nested select
            product_id,
            build['id'],
            machine['platform'],
            build_type
            ]

        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_build_data',
            debug_show=self.DEBUG,
            placeholders=placeholders
            )

        build_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_build_data',
            debug_show=self.DEBUG,
            return_type='iter',
            placeholders=[
                product_id, build['id'], machine['platform'], build_type
                ]
            )

        id = build_iter.get_column_data('id')

        return id


    def _get_or_create_machine_id(self, data, os_id):
        """
        Given a TestData instance, returns the test id from the db.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        machine = data['test_machine']

        # Insert the the machine name and timestamp if it doesn't exist
        date_added = utils.get_now_timestamp()
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

    ##b2g project specific methods##

    def _update_b2g_test_run(self, data, test_run_id):

        if 'gecko_revision' in data['test_build']:

            gecko_proc = 'perftest.inserts.set_gecko_revision'

            gecko_revision = data['test_build']['gecko_revision']

            test_dict = self.sources["perftest"].dhub.execute(
                proc=gecko_proc,
                debug_show=self.DEBUG,
                placeholders=[ gecko_revision, test_run_id ]
                )

        if 'build_revision' in data['test_build']:

            build_proc = 'perftest.inserts.set_build_revision'

            build_revision = data['test_build']['build_revision']

            test_dict = self.sources["perftest"].dhub.execute(
                proc=build_proc,
                debug_show=self.DEBUG,
                placeholders=[ build_revision, test_run_id ]
                )

    def _update_b2g_machine_type(self, data, machine_id):

        if 'type' in data['test_machine']:
            machine_type_proc = 'perftest.inserts.set_machine_type'

            self.sources["perftest"].dhub.execute(
                proc=machine_type_proc,
                debug_show=self.DEBUG,
                placeholders=[ data['test_machine']['type'], machine_id ]
                )

    def _get_median_from_sorted_list(self, sorted_list):

        length = len(sorted_list)
        if not length % 2:
            return round(
            (sorted_list[length / 2] + sorted_list[length / 2 - 1]) / 2.0, 0
                )
        return round( sorted_list[length / 2], 0 )

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
