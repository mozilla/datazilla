import unittest
import sys
import os
import json

from datasource.bases.BaseHub import BaseHub
from datasource.DataHub import DataHub

class TestDataHub(unittest.TestCase):

    testData = []

    ##Set path to data file##
    filePath = os.path.dirname(__file__)

    if filePath:
        dataFile = filePath + '/test_data.txt'
    else:
        dataFile = './test_data.txt'

    @staticmethod
    def loadData():

        dataFileObj = open(TestDataHub.dataFile)
        try:
            for line in dataFileObj.read().split("\n"):
                if line:
                    TestDataHub.testData.append(line.split("\t"))
        finally:
            dataFileObj.close()

        TestDataHub.testDataRows = len(TestDataHub.testData)

    @staticmethod
    def getSuite():
        """
        The order of the tests is critical.  Build a test suite that insures
        proper execution order.

        Parameters:
           None

        Returns:
           test suite
        """
        tests = ['testParseDataSources',
                 'testDbExistance',
                 'testCreateDataTable',
                 'testLoadData',
                 'testDropTable' ]

        return unittest.TestSuite(map(TestDataHub, tests))

    def setUp(self):

        ####
        #TODO:
        #Most of the attribute initializations would be better placed
        #in __init__.  However, I get a doc string related error when
        #I try that from the base class, not sure why.  Skipping for now.
        ###
        self.testDataRows = 0
        self.dataSource = 'MySQL_test'
        self.db = 'test'
        self.tableName = 'DATA_SOURCES_TEST_DATA'
        self.callbackCalls = 0
        self.limit = 100
        self.columns = set(['category', 'term', 'go_id', 'id', 'auto_pfamA'])

    def tearDown(self):
        sys.stdout.flush()

    def testParseDataSources(self):

        ##Instantiating base hub triggers data_sources.json parsing##
        bh = BaseHub()
        if self.dataSource not in BaseHub.dataSources:
            msg = "The required data source, %s, was not found in %s" % (self.dataSource, BaseHub.sourceListFile)
            fail(msg)

    def testDbExistance(self):

        dh = DataHub.get(self.dataSource)
        dbs = dh.getDatabases()

        if 'test' not in dbs:
            msg = "No 'test' database found in %s.  To run this method create a 'test' db in %s." % (self.dataSource, self.dataSource)
            self.fail(msg)

    def testCreateDataTable(self):

        dh = DataHub.get(self.dataSource)
        dh.execute(db=self.db,
                   proc="test.create_table")

        tableSet = dh.execute(db=self.db,
                             proc="sql.ds_selects.get_tables",
                             key_column="Tables_in_test",
                             return_type="set")

        if self.tableName not in tableSet:
            msg = "The table, %s, was not created in %s." % (self.tableName, self.db)
            self.fail(msg)

    def testLoadData(self):

        dh = DataHub.get(self.dataSource)
        dh.useDatabase('test')

        ##Load Data##
        for row in TestDataHub.testData:
            dh.execute(proc="test.insert_test_data",
                       placeholders=row)

        rowcount = dh.execute( db=self.db,
                            proc="sql.ds_selects.get_row_count",
                            replace=['auto_pfamA', self.tableName],
                            return_type='iter').getColumnData('rowcount')

        ##Confirm we loaded all of the rows##
        msg = 'Row count in data file, %i, does not match row count in db %i.' % (TestDataHub.testDataRows, rowcount)
        self.assertEqual(rowcount, TestDataHub.testDataRows, msg=msg)

    def testDropTable(self):

        dh = DataHub.get(self.dataSource)
        dh.execute(db=self.db,
                   proc="test.drop_table")

        tableSet = dh.execute(db=self.db,
                             proc="sql.ds_selects.get_tables",
                             key_column="Tables_in_test",
                             return_type="set")

        if self.tableName in tableSet:
            msg = "The table, %s, was not dropped in %s." % (self.tableName, self.db)
            self.fail(msg)

def main():
    ##Load test data one time##
    TestDataHub.loadData()

    suite = TestDataHub.getSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()