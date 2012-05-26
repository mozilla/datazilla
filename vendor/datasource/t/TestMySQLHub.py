import unittest
import sys
import os
import json

from datasource.bases.BaseHub import BaseHub
from datasource.bases.RDBSHub import RDBSHub, RDBSHubExecuteError
from datasource.DataHub import DataHub

from datasource.hubs.MySQL import MySQL


class TestMySQLHub(unittest.TestCase):

    testData = []

    ##Set path to data file##
    filePath = os.path.dirname(__file__)

    if filePath:
        dataFile = filePath + '/test_data.txt'
    else:
        dataFile = './test_data.txt'

    @staticmethod
    def loadData():

        dataFileObj = open(TestMySQLHub.dataFile)
        try:
            for line in dataFileObj.read().split("\n"):
                if line:
                    TestMySQLHub.testData.append(line.split("\t"))
        finally:
            dataFileObj.close()

        TestMySQLHub.testDataRows = len(TestMySQLHub.testData)

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
                 'testExecuteRules',
                 'testCreateDataTable',
                 'testLoadData',
                 'testIterReturnType',
                 'testDictReturnType',
                 'testDictJsonReturnType',
                 'testTupleReturnType',
                 'testTupleJsonReturnType',
                 'testSetReturnType',
                 'testSetJsonReturnType',
                 'testTableReturnType',
                 'testTableJsonReturnType',
                 'testCallbackReturnType',
                 'testChunking',
                 'testChunkingWithMin',
                 'testRawSql',
                 'testReplace',
                 'testReplaceQuote',
                 'testPlaceholderQuote',
                 'testBigReplace',
                 'testDropTable',
                 'testDisconnect']

        return unittest.TestSuite(map(TestMySQLHub, tests))

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
        self.nsets = 986
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

        dh = MySQL(self.dataSource)
        dbs = dh.getDatabases()

        if 'test' not in dbs:
            msg = "No 'test' database found in %s.  To run this method create a 'test' db in %s." % (self.dataSource, self.dataSource)
            self.fail(msg)

    def testExecuteRules(self):

        rh = RDBSHub(self.dataSource)

        ###
        #See RDBSHub.setExecuteRules for test descriptions
        ###

        #########
        #These are some hacky one way logic tests.
        #All tests should raise RDBSHubExecuteError
        #########

        # 1.) make sure we recognize all of the args, chicken being the exception here
        args = dict(chicken=1, proc='fake.proc', return_type='tuple')
        self.__tryIt(rh, args)

        # 2.) proc or sql must be provided or we have nothing to execute
        args = dict(return_type='tuple', db=self.db)
        self.__tryIt(rh, args)

        # 3.) placeholders and replace must be set to lists
        args = dict(placeholders=dict())
        self.__tryIt(rh, args)
        args = dict(replace=dict())
        self.__tryIt(rh, args)

        # 4.) key_column is required if the return type is dict, dict_json,
        # set, or set_json
        for key in rh.returnTypeKeyColumns:
            args = dict(return_type=key, proc='fake.proc')
            self.__tryIt(rh, args)

        # 5.) If a return type of callback is selected a callback key must be
        # provided wih a function reference
        args = dict(return_type='callback', proc='fake.proc')
        self.__tryIt(rh, args)

        # 6.) chunk_size must be provided with a chunk_source
        args = dict(chunk_size=100, proc='fake.proc')
        self.__tryIt(rh, args)
        args = dict(chunk_source='table.column', proc='fake.proc')
        self.__tryIt(rh, args)

    def testCreateDataTable(self):

        dh = MySQL(self.dataSource)
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

        dh = MySQL(self.dataSource)
        dh.useDatabase('test')

        ##Load Data##
        for row in TestMySQLHub.testData:
            dh.execute(proc="test.insert_test_data",
                       placeholders=row)

        rowcount = dh.execute( db=self.db,
                            proc="sql.ds_selects.get_row_count",
                            replace=['auto_pfamA', self.tableName],
                            return_type='iter').getColumnData('rowcount')

        ##Confirm we loaded all of the rows##
        msg = 'Row count in data file, %i, does not match row count in db %i.' % (TestMySQLHub.testDataRows, rowcount)
        self.assertEqual(rowcount, TestMySQLHub.testDataRows, msg=msg)

    def testTableIter(self):

        dh = MySQL(self.dataSource)

        iter = dh.execute( db=self.db,
                           proc="test.get_data",
                           return_type='iter')

        msg = 'Row count in iter, %i, does not match row count in db %i.' % (iter.rowcount, TestMySQLHub.testDataRows)
        self.assertEqual(iter.rowcount, TestMySQLHub.testDataRows, msg=msg)

        rowcount = 0
        for data in iter:
            rowcount += 1

        msg = 'The iterations in iter, %i, do not match the row count in db %i.' % (rowcount, TestMySQLHub.testDataRows)
        self.assertEqual(iter.rowcount, TestMySQLHub.testDataRows, msg=msg)

    def testIterReturnType(self):

        dh = MySQL(self.dataSource)

        iter = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           return_type='iter')
        rowcount = 0
        columns = set()
        for row in iter:
            if rowcount == 0:
                map(lambda c:columns.add(c), row.keys())
            rowcount += 1

        msg = 'The iter.rowcount, %i, do not match the row count %i.' % (iter.rowcount, self.limit)
        self.assertEqual(iter.rowcount, self.limit, msg=msg)

        msg = 'The iterations in iter, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

        msg = 'The column names in iter, %s, do not match %s.' % (','.join(columns), ','.join(self.columns))
        self.assertEqual(columns, self.columns)

        iter = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=1,
                           return_type='iter')

        term = iter.getColumnData('term')
        if not term:
            msg = 'iter.getColumnData failed to retrieve `term` column.'
            fail(msg)

    def testDictReturnType(self):

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           key_column='id',
                           return_type='dict')
        rowcount = len(data)
        columns = set(data[1].keys())

        msg = 'return value must be a dict'
        self.assertEqual(type(data), type(dict()), msg=msg)

        msg = 'The items in data dictionary, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

        msg = 'The column names in data dictionary, %s, do not match %s.' % (','.join(columns), ','.join(self.columns))
        self.assertEqual(columns, self.columns)

    def testDictJsonReturnType(self):

        dh = MySQL(self.dataSource)

        j = dh.execute( db=self.db,
                        proc="test.get_data",
                        limit=self.limit,
                        key_column='id',
                        return_type='dict_json')

        data = json.loads(j)
        rowcount = len(data)

        ##Keys will be unicode since it's coming from json##
        columns = set(data[u'1'].keys())

        msg = 'The items in data dictionary, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

        msg = 'The column names in data dictionary, %s, do not match %s.' % (','.join(columns), ','.join(self.columns))
        self.assertEqual(columns, self.columns)

    def testTupleReturnType(self):

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           return_type='tuple')

        rowcount = len(data)
        columns = set(data[0].keys())

        msg = 'return value must be a tuple'
        self.assertEqual(type(data), type(tuple()), msg=msg)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

        msg = 'The column names in data tuple, %s, do not match %s.' % (','.join(columns), ','.join(self.columns))
        self.assertEqual(columns, self.columns)

    def testTupleJsonReturnType(self):

        dh = MySQL(self.dataSource)

        j = dh.execute( db=self.db,
                        proc="test.get_data",
                        limit=self.limit,
                        return_type='tuple_json')

        data = json.loads(j)

        rowcount = len(data)
        columns = set(data[0].keys())

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

        msg = 'The column names in data tuple, %s, do not match %s.' % (','.join(columns), ','.join(self.columns))
        self.assertEqual(columns, self.columns)

    def testSetReturnType(self):

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           key_column='id',
                           return_type='set')

        msg = 'return value must be a set'
        self.assertEqual(type(data), type(set()), msg=msg)

        rowcount = len(data)

        msg = 'The items in data set, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def testSetJsonReturnType(self):

        dh = MySQL(self.dataSource)

        j = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           key_column='id',
                           return_type='set_json')

        data = json.loads(j)
        rowcount = len(data)

        msg = 'The items in data set, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def testTableReturnType(self):

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           return_type='table')

        if 'columns' not in data:
            msg = "The columns key was not found in data."
            self.fail(msg)
        if 'data' not in data:
            msg = "The data key was not found in data."
            self.fail(msg)

        rowcount = len( data['data'] )

        msg = 'The items in data set, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def testTableJsonReturnType(self):

        dh = MySQL(self.dataSource)

        j = dh.execute( db=self.db,
                        proc="test.get_data",
                        limit=self.limit,
                        return_type='table_json')

        data = json.loads(j)

        if 'columns' not in data:
            msg = "The columns key was not found in data."
            self.fail(msg)
        if 'data' not in data:
            msg = "The data key was not found in data."
            self.fail(msg)

        rowcount = len( data['data'] )

        msg = 'The items in data set, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def testCallbackReturnType(self):

        dh = MySQL(self.dataSource)

        dh.execute( db=self.db,
                    proc="test.get_data",
                    callback=self.__callbackTest,
                    limit=self.limit,
                    return_type='callback')

        msg = 'self.callbackCalls, %i, does not match the row count %i.' % (self.callbackCalls, self.limit)
        self.assertEqual(self.callbackCalls, self.limit, msg=msg)

    def testChunking(self):

        chunkSize = 10
        dh = MySQL(self.dataSource)

        nsets = 0
        for d in  dh.execute( db=self.db,
                              proc="test.get_data",
                              chunk_size=10,
                              chunk_source='DATA_SOURCES_TEST_DATA.id'):

            nsets += 1

        msg = 'total chunk sets should be, %i, there were %i chunk sets found.' % (self.nsets, nsets)
        self.assertEqual(self.nsets, nsets, msg=msg)

    def testChunkingWithMin(self):

        chunkSize = 10
        dh = MySQL(self.dataSource)

        nsets = 0
        for d in  dh.execute( db=self.db,
                              proc="test.get_data",
                              chunk_size=100,
                              chunk_min=5,
                              chunk_source='DATA_SOURCES_TEST_DATA.id'):

            nsets += 1

        msg = 'total chunk sets should be, %i, there were %i chunk sets found.' % (99, nsets)
        self.assertEqual(99, nsets, msg=msg)

    def testRawSql(self):

        sql = """SELECT `id`, `auto_pfamA`, `go_id`, `term`, `category`
                 FROM `test`.`DATA_SOURCES_TEST_DATA`"""

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           sql=sql,
                           limit=self.limit,
                           return_type='tuple')

        rowcount = len(data)
        columns = set(data[0].keys())

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

        msg = 'The column names in data tuple, %s, do not match %s.' % (','.join(columns), ','.join(self.columns))
        self.assertEqual(columns, self.columns)

    def testReplace(self):

        repValues = ['id',
                     'auto_pfamA',
                     'go_id',
                     'term',
                     'category',
                     'DATA_SOURCES_TEST_DATA']

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_data_replace",
                           limit=self.limit,
                           replace=repValues,
                           return_type='tuple')

        rowcount = len(data)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def testReplaceQuote(self):

        repValues = [ "GO:0015075",
                       "GO:0032934",
                       "GO:0003700",
                       "GO:0000795" ]

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_replace_quote",
                           replace_quote=[repValues],
                           return_type='tuple')

        rows = 90
        rowcount = len(data)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, rows)
        self.assertEqual(rowcount, rows, msg=msg)

    def testPlaceholderQuote(self):

        p = [ "GO:0015075",
              "GO:0032934",
              "GO:0003700",
              "GO:0000795" ]

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_placeholder_quote",
                           placeholders=p,
                           return_type='tuple')

        rows = 90
        rowcount = len(data)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, rows)
        self.assertEqual(rowcount, rows, msg=msg)

    def testBigReplace(self):

        ids = [1,2,3,4,5,6,7,8,9,10]

        repValues = ['id',
                     'auto_pfamA',
                     'go_id',
                     'term',
                     'category',
                     'DATA_SOURCES_TEST_DATA',
                     ids]

        dh = MySQL(self.dataSource)

        data = dh.execute( db=self.db,
                           proc="test.get_big_replace",
                           limit=self.limit,
                           replace=repValues,
                           return_type='tuple')

        rowcount = len(data)

    def testDropTable(self):

        dh = MySQL(self.dataSource)

        dh.execute(db=self.db,
                   proc="test.drop_table")

        tableSet = dh.execute(db=self.db,
                             proc="sql.ds_selects.get_tables",
                             key_column="Tables_in_test",
                             return_type="set")

        if self.tableName in tableSet:
            msg = "The table, %s, was not dropped in %s." % (self.tableName, self.db)
            self.fail(msg)

    def testDisconnect(self):

        dh = MySQL(self.dataSource)
        dh.disconnect()

    def __callbackTest(self, row):
        self.callbackCalls += 1

    def __tryIt(self, rh, args):
        try:
            rh.setExecuteRules(args)
        except RDBSHubExecuteError, err:
            ##Yay! test worked
            pass
        else:
            ##OOh we should have an error here##
            self.fail("\tShould have raised RDBSHubExecuteError on args:%s" % (','.join(args.keys())))

def main():
    ##Load test data one time##
    TestMySQLHub.loadData()

    suite = TestMySQLHub.getSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
