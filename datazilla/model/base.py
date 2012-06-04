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
    def __init__(self, project):
        self.project = project
        self.sources = {
            "perftest": self.datasource_class(project, "perftest"),
            }
        self.DEBUG = settings.DEBUG


    def __unicode__(self):
        """Unicode representation is project name."""
        return self.project


    @property
    def datasource_class(self):
        if settings.USE_APP_ENGINE:
            from .appengine.model import CloudSQLDataSource
            return CloudSQLDataSource
        else:
            from .sql.models import SQLDataSource
            return SQLDataSource


    @property
    def dhub(self):
        return self.sources["perftest"].dhub


    def getProductTestOsMap(self):

        proc = 'perftest.selects.get_product_test_os_map'

        productTuple = self.dhub.execute(proc=proc,
                                         debug_show=self.DEBUG,
                                         return_type='tuple')

        return productTuple


    def getOperatingSystems(self, keyColumn=None):

        operatingSystems = dict()

        proc = 'perftest.selects.get_operating_systems'

        if keyColumn:
            operatingSystems = self.dhub.execute(proc=proc,
                                                 debug_show=self.DEBUG,
                                                 key_column=keyColumn,
                                                 return_type='dict')
        else:
            osTuple = self.dhub.execute(proc=proc,
                                        debug_show=self.DEBUG,
                                        return_type='tuple')

            operatingSystems = self._getUniqueKeyDict(osTuple,
                                                      ['name', 'version'])

        return operatingSystems


    def getTests(self, keyColumn='name'):

        proc = 'perftest.selects.get_tests'

        testDict = self.dhub.execute(proc=proc,
                                     debug_show=self.DEBUG,
                                     key_column=keyColumn,
                                     return_type='dict')

        return testDict


    def getProducts(self, keyColumn=None):

        products = dict()

        proc = 'perftest.selects.get_product_data'

        if keyColumn:
            products = self.dhub.execute(proc=proc,
                                         debug_show=self.DEBUG,
                                         key_column=keyColumn,
                                         return_type='dict')
        else:
            productsTuple = self.dhub.execute(proc=proc,
                                              debug_show=self.DEBUG,
                                              return_type='tuple')

            products = self._getUniqueKeyDict(productsTuple,
                                             ['product', 'branch', 'version'])

        return products


    def getMachines(self):

        proc = 'perftest.selects.get_machines'

        machinesDict = self.dhub.execute(proc=proc,
                                         debug_show=self.DEBUG,
                                         key_column='name',
                                         return_type='dict')

        return machinesDict


    def getOptions(self):

        proc = 'perftest.selects.get_options'

        optionsDict = self.dhub.execute(proc=proc,
                                        debug_show=self.DEBUG,
                                        key_column='name',
                                        return_type='dict')

        return optionsDict


    def getPages(self):

        proc = 'perftest.selects.get_pages'

        pagesDict = self.dhub.execute(proc=proc,
                                      debug_show=self.DEBUG,
                                      key_column='url',
                                      return_type='dict')

        return pagesDict


    def getAuxData(self):

        proc = 'perftest.selects.get_aux_data'

        auxDataDict = self.dhub.execute(proc=proc,
                                        debug_show=self.DEBUG,
                                        key_column='name',
                                        return_type='dict')

        return auxDataDict


    def getReferenceData(self):

        referenceData = dict( operating_systems=self.getOperatingSystems(),
                              tests=self.getTests(),
                              products=self.getProducts(),
                              machines=self.getMachines(),
                              options=self.getOptions(),
                              pages=self.getPages(),
                              aux_data=self.getAuxData())

        return referenceData


    def getTestCollections(self):

        proc = 'perftest.selects.get_test_collections'

        testCollectionTuple = self.dhub.execute(proc=proc,
                                                debug_show=self.DEBUG,
                                                return_type='tuple')

        testCollection = dict()
        for data in testCollectionTuple:

            if data['id'] not in testCollection:

                id = data['id']
                testCollection[ id ] = dict()
                testCollection[ id ]['name'] = data['name']
                testCollection[ id ]['description'] = data['description']
                testCollection[ id ]['data'] = []

            productId = data['product_id']
            osId = data['operating_system_id']

            testCollection[ id ]['data'].append({'test_id':data['test_id'],
                                                 'name':data['name'],
                                                 'product_id':productId,
                                                 'operating_system_id':osId })


        return testCollection


    def getTestReferenceData(self):

        referenceData = dict(operating_systems=self.getOperatingSystems('id'),
                             tests=self.getTests('id'),
                             products=self.getProducts('id'),
                             product_test_os_map=self.getProductTestOsMap(),
                             test_collections=self.getTestCollections())

        return referenceData


    def getTestRunSummary(self,
                          start,
                          end,
                          productIds,
                          operatingSystemIds,
                          testIds):

        colData = {
           'b.product_id': utils.get_id_string(productIds),

           'b.operating_system_id': utils.get_id_string(operatingSystemIds),

           'tr.test_id': utils.get_id_string(testIds)
        }

        rep = utils.build_replacement(colData)

        proc = 'perftest.selects.get_test_run_summary'

        testRunSummaryTable = self.dhub.execute(proc=proc,
                                                debug_show=self.DEBUG,
                                                replace=[ str(end),
                                                          str(start), rep ],
                                                return_type='table')

        return testRunSummaryTable


    def getAllTestRuns(self):

        proc = 'perftest.selects.get_all_test_runs'

        testRunSummaryTable = self.dhub.execute(proc=proc,
                                                debug_show=self.DEBUG,
                                                return_type='table')

        return testRunSummaryTable


    def getTestRunValues(self, testRunId):

        proc = 'perftest.selects.get_test_run_values'

        testRunValueTable = self.dhub.execute(proc=proc,
                                              debug_show=self.DEBUG,
                                              placeholders=[ testRunId ],
                                              return_type='table')

        return testRunValueTable


    def getTestRunValueSummary(self, testRunId):

        proc = 'perftest.selects.get_test_run_value_summary'

        testRunValueTable = self.dhub.execute(proc=proc,
                                              debug_show=self.DEBUG,
                                              placeholders=[ testRunId ],
                                              return_type='table')

        return testRunValueTable


    def getPageValues(self, testRunId, pageId):

        proc = 'perftest.selects.get_page_values'

        pageValuesTable = self.dhub.execute(proc=proc,
                                            debug_show=self.DEBUG,
                                            placeholders=[ testRunId,
                                                           pageId ],
                                            return_type='table')

        return pageValuesTable


    def getSummaryCache(self, itemId, itemData):

        proc = 'perftest.selects.get_summary_cache'

        cachedData = self.dhub.execute(proc=proc,
                                       debug_show=self.DEBUG,
                                       placeholders=[ itemId, itemData ],
                                       return_type='tuple')

        return cachedData


    def getAllSummaryCache(self):

        proc = 'perftest.selects.get_all_summary_cache_data'

        dataIter = self.dhub.execute(proc=proc,
                                     debug_show=self.DEBUG,
                                     chunk_size=5,
                                     chunk_source="summary_cache.id",
                                     return_type='tuple')


        return dataIter


    def getAllTestData(self, start, total):

        proc = 'perftest.selects.get_all_test_data'

        dataIter = self.dhub.execute(proc=proc,
                                     debug_show=self.DEBUG,
                                     placeholders=[start],
                                     chunk_size=20,
                                     chunk_min=start,
                                     chunk_source="test_data.id",
                                     chunk_total=total,
                                     return_type='tuple')

        return dataIter


    def setSummaryCache(self, itemId, itemData, value):

        nowDatetime = str( datetime.datetime.now() )

        self.sources["perftest"].set_data('set_summary_cache', [ itemId,
                                            itemData,
                                            value,
                                            nowDatetime,
                                            value,
                                            nowDatetime ])

    def set_test_collection(self, name, description):

        id = self.sources["perftest"].set_data_and_get_id('set_test_collection',
                                                        [ name,
                                                          description,
                                                          name ])

        return id

    def set_test_collection_map(self, test_collection_id, product_id):

        self.sources["perftest"].set_data('set_test_collection_map',
                                          [ test_collection_id,
                                            product_id ])

    def disconnect(self):
        return self.sources["perftest"].disconnect()


    def loadTestData(self, data, jsonData):

        ##Get the reference data##
        refData = self.getReferenceData()

        ##Get/Set reference info##
        refData['test_id'] = self._getTestId(data, refData)
        refData['option_id_map'] = self._getOptionIds(data, refData)
        refData['operating_system_id'] = self._getOsId(data, refData)
        refData['product_id'] = self._getProductId(data, refData)
        refData['machine_id'] = self._getMachineId(data, refData)

        refData['build_id'] = self._setBuildData(data, refData)
        refData['test_run_id'] = self._setTestRunData(data, refData)

        self._setOptionData(data, refData)
        self._setTestValues(data, refData)
        self._setTestAuxData(data, refData)
        self._setTestData(jsonData, refData)

    def _setTestData(self, jsonData, refData):

        self.sources["perftest"].set_data('set_test_data',
                            [refData['test_run_id'], jsonData])


    def _setTestAuxData(self, data, refData):

        if 'results_aux' in data:

            for auxData in data['results_aux']:
                auxDataId = self._getAuxId(auxData, refData)
                auxValues = data['results_aux'][auxData]

                placeholders = []
                for index in range(0, len(auxValues)):

                    stringData = ""
                    numericData = 0
                    if utils.is_number(auxValues[index]):
                        numericData = auxValues[index]
                    else:
                        stringData = auxValues[index]

                    placeholders.append( (refData['test_run_id'],
                                          index + 1,
                                          auxDataId,
                                          numericData,
                                          stringData))

                self.sources["perftest"].set_data('set_aux_values',
                                                  placeholders,
                                                  True)

    def _setTestValues(self, data, refData):

        for page in data['results']:

            pageId = self._getPageId(page, refData)

            values = data['results'][page]

            placeholders = []
            for index in range(0, len(values)):
                value = values[index]
                placeholders.append( (refData['test_run_id'],
                                      index + 1,
                                      pageId,
                                      ######
                                      #TODO: Need to get the value
                                      #id into the json
                                      ######
                                      1,
                                      value))

            self.sources["perftest"].set_data('set_test_values',
                                              placeholders,
                                              True)


    def _getAuxId(self, auxData, refData):

        auxId = 0
        try:
            if auxData in refData['aux_data']:
                auxId = refData['aux_data'][auxData]['id']
            else:
                auxId = self.sources["perftest"].set_data_and_get_id('set_aux_data',
                                             [refData['test_id'],
                                             auxData])

        except KeyError:
            raise
        else:
            return auxId


    def _getPageId(self, page, refData):

        pageId = 0
        try:
            if page in refData['pages']:
                pageId = refData['pages'][page]['id']
            else:
                pageId = self.sources["perftest"].set_data_and_get_id('set_pages_data',
                                              [refData['test_id'], page])

        except KeyError:
            raise
        else:
            return pageId


    def _setOptionData(self, data, refData):

        if 'options' in data['testrun']:
            for option in data['testrun']['options']:
                id = refData['option_id_map'][option]['id']
                value = data['testrun']['options'][option]
                self.sources["perftest"].set_data('set_test_option_values',
                                                  [refData['test_run_id'],
                                                   id,
                                                   value])


    def _setBuildData(self, data, refData):

        buildId = self.sources["perftest"].set_data_and_get_id('set_build_data',
                                       [ refData['operating_system_id'],
                                         refData['product_id'],
                                         refData['machine_id'],
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

        return buildId


    def _setTestRunData(self, data, refData):

        testRunId = self.sources["perftest"].set_data_and_get_id('set_test_run_data',
                                         [ refData['test_id'],
                                         refData['build_id'],
                                         data['test_build']['revision'],
                                         data['testrun']['date'] ])

        return testRunId


    def _getMachineId(self, data, refData):

        machineId = 0
        try:
            name = data['test_machine']['name']
            if name in refData['machines']:
                machineId = refData['machines'][ name ]['id']
            else:
                machineId = self.sources["perftest"].set_data_and_get_id('set_machine_data',
                                                 [ name, int(time.time()) ])

        except KeyError:
            raise

        else:
            return machineId


    def _getTestId(self, data, refData):
        testId = 0
        try:
            if data['testrun']['suite'] in refData['tests']:
                testId = refData['tests'][ data['testrun']['suite'] ]['id']
            else:
                ###
                #TODO: version should be set in the data structure
                #      provided.  This currently hard codes it to 1
                #      for all tests
                ###
                version = 1
                if 'suite_version' in data['testrun']:
                    version = int(data['testrun']['suite_version'])

                testId = self.sources["perftest"].set_data_and_get_id('set_test',
                                      [ data['testrun']['suite'], version ])

        except KeyError:
            raise
        else:
            return testId


    def _getOsId(self, data, refData):

        osId = 0
        try:
            osName = data['test_machine']['os']
            osVersion = data['test_machine']['osversion']
            osKey = osName + osVersion
            if osKey in refData['operating_systems']:
                osId = refData['operating_systems'][osKey]
            else:
                osId = self.sources["perftest"].set_data_and_get_id('set_operating_system',
                                            [ osName, osVersion ])

        except KeyError:
            raise

        else:
            return osId


    def _getOptionIds(self, data, refData):
        optionIds = dict()
        try:
            if 'options' in data['testrun']:
                for option in data['testrun']['options']:
                    if option in refData['options']:
                        optionIds[ option ] = refData['options'][option]
                    else:
                        testId = self.sources["perftest"].set_data_and_get_id('set_option_data', [ option ])
                        optionIds[ option ] = testId
        except KeyError:
            raise
        else:
            return optionIds


    def _getProductId(self, data, refData):

        productId = 0

        try:
            product = data['test_build']['name']
            branch = data['test_build']['branch']
            version = data['test_build']['version']

            productKey = product + branch + version

            if productKey in refData['products']:
                productId = refData['products'][productKey]
            else:
                productId = self.sources["perftest"].set_data_and_get_id('set_product_data',
                                                 [ product, branch, version ])

        except KeyError:
            raise
        else:
            return productId


    def _getUniqueKeyDict(self, dataTuple, keyStrings):

        dataDict = dict()
        for data in dataTuple:
            uniqueKey = ""
            for key in keyStrings:
                uniqueKey += str(data[key])
            dataDict[ uniqueKey ] = data['id']
        return dataDict
