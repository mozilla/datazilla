#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
"""
``DatazillaModel`` (and subclasses) are the public interface for all data
access.

"""
import datetime
import time

from django.conf import settings


from . import utils



class DatazillaModel(object):
    """Public interface to all data access for a project."""

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
        if settings.USE_APP_ENGINE:
            from .appengine.model import CloudSQLDataSource
            return CloudSQLDataSource
        else:
            from .sql.models import SQLDataSource
            return SQLDataSource


    @classmethod
    def create(cls, project):
        """Create all the datasource tables for this project."""

        for ct in cls.CONTENT_TYPES:
            cls.get_datasource_class().create(project, ct)

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
            debug_show=settings.DEBUG,
            placeholders=placeholders,
            executemany=False,
            )


    def set_test_collection(self, name, description):

        id = self.sources["perftest"].get_last_insert_id('set_test_collection',
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
            debug_show=settings.DEBUG,
            placeholders=placeholders,
            executemany=False,
            )


    def disconnect(self):
        """Iterate over and disconnect all data sources."""
        for src in self.sources.itervalues():
            src.disconnect()


    def store_test_data(self, json_data):
        """Write the JSON to the objectstore to be queued for processing."""

        self.sources["objectstore"].dhub.execute(
            proc='objectstore.inserts.store_json',
            debug_show=settings.DEBUG,
            placeholders=[json_data],
            executemany=False,
            )


    def retrieve_test_data(self, limit):
        """Retrieve the JSON from the objectstore to be processed"""
        proc = 'objectstore.selects.get_unprocessed'

        json_blobs = self.sources["objectstore"].dhub.execute(
            proc=proc,
            placeholders=[ limit ],
            debug_show=self.DEBUG,
            return_type='tuple'
            )

        return json_blobs

    def load_test_data(self, data, json_data):
        """Process the JSON test data into the database."""

        ##Get the reference data##
        ref_data = self.get_reference_data()

        ##Get/Set reference info##
        ref_data['test_id'] = self._get_test_id(data, ref_data)
        ref_data['option_id_map'] = self._get_option_ids(data, ref_data)
        ref_data['operating_system_id'] = self._get_os_id(data, ref_data)
        ref_data['product_id'] = self._get_product_id(data, ref_data)
        ref_data['machine_id'] = self._get_machine_id(data, ref_data)

        ref_data['build_id'] = self._set_build_data(data, ref_data)
        ref_data['test_run_id'] = self._set_test_run_data(data, ref_data)

        self._set_option_data(data, ref_data)
        self._set_test_values(data, ref_data)
        self._set_test_aux_data(data, ref_data)
        self._set_test_data(json_data, ref_data)


    def _set_test_data(self, json_data, ref_data):

        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_test_data',
            debug_show=settings.DEBUG,
            placeholders=[ref_data['test_run_id'], json_data],
            executemany=False,
            )


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

                self.sources["perftest"].dhub.execute(
                    proc='perftest.inserts.set_aux_values',
                    debug_show=settings.DEBUG,
                    placeholders=placeholders,
                    executemany=True,
                    )


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

            self.sources["perftest"].dhub.execute(
                proc='perftest.inserts.set_test_values',
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )


    def _get_aux_id(self, aux_data, ref_data):

        aux_id = 0
        try:
            if aux_data in ref_data['aux_data']:
                aux_id = ref_data['aux_data'][aux_data]['id']
            else:
                aux_id = self.sources["perftest"].get_last_insert_id('set_aux_data',
                                             [ref_data['test_id'],
                                             aux_data])

        except KeyError:
            raise
        else:
            return aux_id


    def _get_page_id(self, page, ref_data):

        page_id = 0
        try:
            if page in ref_data['pages']:
                page_id = ref_data['pages'][page]['id']
            else:
                page_id = self.sources["perftest"].get_last_insert_id('set_pages_data',
                                              [ref_data['test_id'], page])

        except KeyError:
            raise
        else:
            return page_id


    def _set_option_data(self, data, ref_data):

        if 'options' in data['testrun']:
            for option in data['testrun']['options']:
                id = ref_data['option_id_map'][option]['id']
                value = data['testrun']['options'][option]

                placeholders = [
                    ref_data['test_run_id'],
                    id,
                    value,
                    ]

                self.sources["perftest"].dhub.execute(
                    proc='perftest.inserts.set_test_option_values',
                    debug_show=settings.DEBUG,
                    placeholders=placeholders,
                    executemany=False,
                    )


    def _set_build_data(self, data, ref_data):

        build_id = self.sources["perftest"].get_last_insert_id('set_build_data',
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

        test_run_id = self.sources["perftest"].get_last_insert_id('set_test_run_data',
                                         [ ref_data['test_id'],
                                         ref_data['build_id'],
                                         data['test_build']['revision'],
                                         data['testrun']['date'] ])

        return test_run_id


    def _get_machine_id(self, data, ref_data):

        machine_id = 0
        try:
            name = data['test_machine']['name']
            if name in ref_data['machines']:
                machine_id = ref_data['machines'][ name ]['id']
            else:
                machine_id = self.sources["perftest"].get_last_insert_id('set_machine_data',
                                                 [ name, int(time.time()) ])

        except KeyError:
            raise

        else:
            return machine_id


    def _get_test_id(self, data, ref_data):
        test_id = 0
        try:
            if data['testrun']['suite'] in ref_data['tests']:
                test_id = ref_data['tests'][ data['testrun']['suite'] ]['id']
            else:
                ###
                #TODO: version should be set in the data structure
                #      provided.  This currently hard codes it to 1
                #      for all tests
                ###
                version = 1
                if 'suite_version' in data['testrun']:
                    version = int(data['testrun']['suite_version'])

                test_id = self.sources["perftest"].get_last_insert_id('set_test',
                                      [ data['testrun']['suite'], version ])

        except KeyError:
            raise
        else:
            return test_id


    def _get_os_id(self, data, ref_data):

        os_id = 0
        try:
            os_name = data['test_machine']['os']
            os_version = data['test_machine']['osversion']
            os_key = os_name + os_version
            if os_key in ref_data['operating_systems']:
                os_id = ref_data['operating_systems'][os_key]
            else:
                os_id = self.sources["perftest"].get_last_insert_id('set_operating_system',
                                            [ os_name, os_version ])

        except KeyError:
            raise

        else:
            return os_id


    def _get_option_ids(self, data, ref_data):
        option_ids = dict()
        try:
            if 'options' in data['testrun']:
                for option in data['testrun']['options']:
                    if option in ref_data['options']:
                        option_ids[ option ] = ref_data['options'][option]
                    else:
                        test_id = self.sources["perftest"].get_last_insert_id('set_option_data', [ option ])
                        option_ids[ option ] = test_id
        except KeyError:
            raise
        else:
            return option_ids


    def _get_product_id(self, data, ref_data):

        product_id = 0

        try:
            product = data['test_build']['name']
            branch = data['test_build']['branch']
            version = data['test_build']['version']

            product_key = product + branch + version

            if product_key in ref_data['products']:
                product_id = ref_data['products'][product_key]
            else:
                product_id = self.sources["perftest"].get_last_insert_id('set_product_data',
                                                 [ product, branch, version ])

        except KeyError:
            raise
        else:
            return product_id


    def _get_unique_key_dict(self, data_tuple, key_strings):

        data_dict = dict()
        for data in data_tuple:
            unique_key = ""
            for key in key_strings:
                unique_key += str(data[key])
            data_dict[ unique_key ] = data['id']
        return data_dict
