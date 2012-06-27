#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
"""
``DatazillaModel`` and subclasses are the public API for all data access.

"""
import datetime
import time
import json

from django.conf import settings


from . import utils



class DatazillaModel(object):
    """Public interface to all data access for a project."""

    class TestDataError(ValueError):
        pass


    CONTENT_TYPES = ["perftest", "objectstore"]

    def __init__(self, project):
        self.project = project

        self.sources = {}
        for ct in self.CONTENT_TYPES:
            self.sources[ct] = self.get_datasource_class()(project, ct)

        self.DEBUG = settings.DEBUG


    def __unicode__(self):
        """Unicode representation is project name."""
        return self.project


    @classmethod
    def get_datasource_class(cls):
        if settings.USE_APP_ENGINE:                         # pragma: no cover
            from .appengine.model import CloudSQLDataSource # pragma: no cover
            return CloudSQLDataSource                       # pragma: no cover
        else:
            from .sql.models import SQLDataSource
            return SQLDataSource


    @classmethod
    def create(cls, project, hosts=None, types=None):
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


        """
        hosts = hosts or {}
        types = types or {}

        for ct in cls.CONTENT_TYPES:
            cls.get_datasource_class().create(
                project, ct, host=hosts.get(ct), db_type=types.get(ct))

        return cls(project=project)


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


    def get_reference_data(self):

        reference_data = dict( operating_systems=self.get_operating_systems(),
                              tests=self.get_tests(),
                              products=self.get_products(),
                              machines=self.get_machines(),
                              options=self.get_options(),
                              pages=self.get_pages(),
                              aux_data=self.get_aux_data())

        return reference_data


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

            test_collection[ id ]['data'].append({'test_id':data['test_id'],
                                                 'name':data['name'],
                                                 'product_id':product_id,
                                                 'operating_system_id':os_id })


        return test_collection


    def get_test_reference_data(self):

        reference_data = dict(operating_systems=self.get_operating_systems('id'),
                             tests=self.get_tests('id'),
                             products=self.get_products('id'),
                             product_test_os_map=self.get_product_test_os_map(),
                             test_collections=self.get_test_collections())

        return reference_data


    def get_test_run_summary(self,
                          start,
                          end,
                          product_ids,
                          operating_system_ids,
                          test_ids):

        col_data = {
           'b.product_id': utils.get_id_string(product_ids),

           'b.operating_system_id': utils.get_id_string(operating_system_ids),

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


    def get_all_test_data(self, start, total):

        proc = 'perftest.selects.get_all_test_data'

        data_iter = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[start],
            chunk_size=20,
            chunk_min=start,
            chunk_source="test_data.id",
            chunk_total=total,
            return_type='tuple',
            )

        return data_iter


    def set_summary_cache(self, item_id, item_data, value):

        now_datetime = str( datetime.datetime.now() )

        placeholders = [
            item_id,
            item_data,
            value,
            now_datetime,
            value,
            now_datetime,
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


    def disconnect(self):
        """Iterate over and disconnect all data sources."""
        for src in self.sources.itervalues():
            src.disconnect()


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
        """Process JSON test data into the perftest database."""

        # reference id data required by insert methods in ref_data
        ref_data = dict()

        # Get/Set reference info, all inserts use an on duplicate key
        # approach
        ref_data['test_id'] = self._get_or_create_test_id(data)
        ref_data['option_ids'] = self._get_or_create_option_ids(data)
        ref_data['operating_system_id'] = self._get_or_create_os_id(data)
        ref_data['product_id'] = self._get_or_create_product_id(data)
        ref_data['machine_id'] = self._get_or_create_machine_id(data)

        # Insert build and test_run data.  All other test data
        # types require the build_id and test_run_id to meet foreign key
        # constriants.
        ref_data['build_id'] = self._set_build_data(data, ref_data)
        ref_data['test_run_id'] = self._set_test_run_data(data, ref_data)

        self._set_option_data(data, ref_data)
        self._set_test_values(data, ref_data)
        self._set_test_aux_data(data, ref_data)

        return ref_data['test_run_id']

    def transfer_objects(self, start_id, limit):
        """
        Transfer objects from test_data table to objectstore.

        TODO: This can go away once all projects have been migrated away from
        using the old test_data table in the perftest schema to using the
        objectstore.

        """
        proc = "perftest.selects.get_test_data"
        data_objects = self.sources["perftest"].dhub.execute(
            proc=proc,
            placeholders=[ int(start_id), int(limit) ],
            debug_show=self.DEBUG,
            return_type='tuple'
            )

        for data_object in data_objects:
            json_data = data_object['data']
            self.store_test_data( json_data )


    def process_objects(self, loadlimit):
        """Processes JSON blobs from the objectstore into perftest schema."""
        rows = self.claim_objects(loadlimit)

        for row in rows:
            data = json.loads(row['json_blob'])
            row_id = int(row['id'])

            if self.verify_json(data):
                test_run_id = self.load_test_data(data)
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
        proc_completed = "objectstore.updates.mark_complete"

        self.sources["objectstore"].dhub.execute(
            proc=proc_completed,
            placeholders=[ test_run_id, object_id ],
            debug_show=self.DEBUG
            )


    def verify_json(self, json_data):
        """ Verify that json is valid for ingestion """
        # TODO (stub)
        # Need to implement some sort of verification json is well-formed
        # to ensure load_test_data won't fail.
        return True


    def _set_test_data(self, json_data, ref_data):

        self._insert_data('set_test_data',
                          [ref_data['test_run_id'], json_data])


    def _set_test_aux_data(self, data, ref_data):

        if 'results_aux' in data:

            for aux_data in data['results_aux']:
                aux_data_id = self._get_aux_id(aux_data, ref_data)
                aux_values = data['results_aux'][aux_data]

                placeholders = []
                for index in range(0, len(aux_values)):

                    string_data = ""
                    numeric_data = 0
                    if utils.is_number(aux_values[index]):
                        numeric_data = aux_values[index]
                    else:
                        string_data = aux_values[index]

                    placeholders.append( (ref_data['test_run_id'],
                                          index + 1,
                                          aux_data_id,
                                          numeric_data,
                                          string_data))

                self._insert_data('set_aux_values',
                                  placeholders,
                                  True)


    def _set_test_values(self, data, ref_data):

        for page in data['results']:

            page_id = self._get_page_id(page, ref_data)

            values = data['results'][page]

            placeholders = []
            for index in range(0, len(values)):
                value = values[index]
                placeholders.append( (ref_data['test_run_id'],
                                      index + 1,
                                      page_id,
                                      ######
                                      #TODO: Need to get the value
                                      #id into the json
                                      ######
                                      1,
                                      value))

            self._insert_data('set_test_values',
                              placeholders,
                              True)


    def _get_aux_id(self, aux_data, ref_data):

        aux_id = 0
        try:
            ##Insert the test id and aux data on duplicate key update##
            insert_proc = 'perftest.inserts.set_aux_ref_data'
            self.sources["perftest"].dhub.execute(
                proc=insert_proc,
                placeholders=[ ref_data['test_id'], aux_data ],
                debug_show=self.DEBUG)

            ##Get the aux data id##
            select_proc = 'perftest.selects.get_aux_data_id'
            id_iter = self.sources["perftest"].dhub.execute(
                proc=select_proc,
                placeholders=[ ref_data['test_id'], aux_data ],
                debug_show=self.DEBUG,
                return_type='iter')

            aux_id = id_iter.get_column_data('id')

        except KeyError:
            raise
        else:
            return aux_id


    def _get_page_id(self, page, ref_data):

        page_id = 0
        try:
            ##Insert the test id and page name on duplicate key update##
            insert_proc = 'perftest.inserts.set_pages_ref_data'
            self.sources["perftest"].dhub.execute(
                proc=insert_proc,
                placeholders=[ ref_data['test_id'], page ],
                debug_show=self.DEBUG)

            ##Get the page id##
            select_proc = 'perftest.selects.get_page_id'
            id_iter = self.sources["perftest"].dhub.execute(
                proc=select_proc,
                placeholders=[ ref_data['test_id'], page ],
                debug_show=self.DEBUG,
                return_type='iter')

            page_id = id_iter.get_column_data('id')

        except KeyError:
            raise
        else:
            return page_id


    def _set_option_data(self, data, ref_data):

        if 'options' in data['testrun']:
            for option in data['testrun']['options']:

                id = ref_data['option_ids'][option]

                value = data['testrun']['options'][option]

                placeholders = [
                    ref_data['test_run_id'],
                    id,
                    value,
                    ]

                self._insert_data( 'set_test_option_values',
                                    placeholders)


    def _set_build_data(self, data, ref_data):

        build_id = self._insert_data_and_get_id('set_build_data',
                                       [ ref_data['operating_system_id'],
                                         ref_data['product_id'],
                                         ref_data['machine_id'],
                                         data['test_build']['id'],
                                         data['test_machine']['platform'],
                                         data['test_build']['revision'],
                                         #####
                                         #TODO: Need to get the
                                         # build_type into the json
                                         #####
                                         'debug',
                                         ##Need to get the build_date into the json##
                                         int(time.time()) ] )

        return build_id


    def _set_test_run_data(self, data, ref_data):

        test_run_id = self._insert_data_and_get_id('set_test_run_data',
                                         [ ref_data['test_id'],
                                         ref_data['build_id'],
                                         data['test_build']['revision'],
                                         data['testrun']['date'] ])

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


    def _get_last_insert_id(self):
        """Return last-inserted ID."""
        return self.sources["perftest"].dhub.execute(
            proc='generic.selects.get_last_insert_id',
            debug_show=self.DEBUG,
            return_type='iter',
            ).get_column_data('id')


    def _get_or_create_machine_id(self, data):
        """
        Given a full test-data structure, returns the test id from the db.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        try:
            machine = data['test_machine']
        except KeyError:
            raise self.TestDataError("Missing 'test_machine' key.")

        try:
            name = machine['name']
        except KeyError:
            raise self.TestDataError("Test machine missing 'name' key.")

        # Insert the the machine name and timestamp on duplicate key update
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_machine_ref_data',
            placeholders=[ name, int(time.time()) ],
            debug_show=self.DEBUG)

        # Get the machine id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_machine_id',
            placeholders=[ name ],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_test_id(self, data):
        """
        Given a full test-data structure, returns the test id from the db.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        try:
            testrun = data['testrun']
        except KeyError:
            raise self.TestDataError("Missing 'testrun' key.")

        try:
            name = testrun["suite"]
        except KeyError:
            raise self.TestDataError("Testrun missing 'suite' key.")

        try:
            # TODO: version should be required; currently defaults to 1
            version = int(testrun.get('suite_version', 1))
        except ValueError:
            raise self.TestDataError(
                "Testrun 'suite_version' is not an integer.")

        # Insert the test name and version on duplicate key update
        self.sources['perftest'].dhub.execute(
            proc='perftest.inserts.set_test_ref_data',
            placeholders=[name, version],
            debug_show=self.DEBUG)

        # Get the test name id
        id_iter = self.sources['perftest'].dhub.execute(
            proc='perftest.selects.get_test_id',
            placeholders=[name, version],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_os_id(self, data):
        """
        Given a full test-data structure, returns the OS id from the database.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        try:
            machine = data['test_machine']
        except KeyError:
            raise self.TestDataError("Missing 'test_machine' key.")

        try:
            os_name = machine['os']
            os_version = machine['osversion']
        except KeyError as e:
            raise self.TestDataError("Test machine missing {0} key.".format(e))

        # Insert the operating system name and version on duplicate key update
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_os_ref_data',
            placeholders=[ os_name, os_version ],
            debug_show=self.DEBUG)

        # Get the operating system name id
        id_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_os_id',
            placeholders=[ os_name, os_version ],
            debug_show=self.DEBUG,
            return_type='iter')

        return id_iter.get_column_data('id')


    def _get_or_create_option_ids(self, data):
        """
        Given test-data structure, returns a dict of {option_name: id}.

        Creates options if necessary. Raises ``TestDataError`` on bad data.

        """
        option_ids = dict()

        try:
            testrun = data['testrun']
        except KeyError:
            raise self.TestDataError("Missing 'testrun' key.")

        options = testrun.get('options', [])

        # Test for a list explicitly because strings are iterable, but we don't
        # want to accidentally create an option for every character in a
        # string.  No need to support other sequence types, a list is the only
        # sequence type returned from json.loads.
        if not isinstance(options, list):
            raise self.TestDataError("Testrun 'options' is not a list.")

        for option in options:

            # Insert the option name on duplicate key update
            self.sources["perftest"].dhub.execute(
                proc='perftest.inserts.set_option_ref_data',
                placeholders=[ option ],
                debug_show=self.DEBUG)

            # Get the option id
            id_iter = self.sources["perftest"].dhub.execute(
                proc='perftest.selects.get_option_id',
                placeholders=[ option ],
                debug_show=self.DEBUG,
                return_type='iter')

            option_ids[option] = id_iter.get_column_data('id')

        return option_ids


    def _get_or_create_product_id(self, data):
        """
        Given a full test-data structure, returns product id from the database.

        Creates it if necessary. Raises ``TestDataError`` on bad data.

        """
        try:
            build = data['test_build']
        except KeyError:
            raise self.TestDataError("Missing 'test_build' key.")

        try:
            product = build['name']
            branch = build['branch']
            version = build['version']
        except KeyError as e:
            raise self.TestDataError("Test build missing {0} key.".format(e))

        # Insert the product, branch, and version on duplicate key update
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_product_ref_data',
            placeholders=[ product, branch, version ],
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
