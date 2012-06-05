import unittest
import sys
import os
import json

from datasource.bases.BaseHub import BaseHub
from datasource.bases.RDBSHub import RDBSHub, RDBSHubExecuteError
from datasource.DataHub import DataHub

from datasource.hubs.MySQL import MySQL


class TestMySQLHub(unittest.TestCase):

    test_data = []

    ##Set path to data file##
    file_path = os.path.dirname(__file__)

    if file_path:
        data_file = file_path + '/test_data.txt'
    else:
        data_file = './test_data.txt'

    @staticmethod
    def load_data():

        data_file_obj = open(TestMySQLHub.data_file)
        try:
            for line in data_file_obj.read().split("\n"):
                if line:
                    TestMySQLHub.test_data.append(line.split("\t"))
        finally:
            data_file_obj.close()

        TestMySQLHub.test_data_rows = len(TestMySQLHub.test_data)

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
        tests = ['test_parse_data_sources',
                 'test_db_existance',
                 'test_execute_rules',
                 'test_create_data_table',
                 'test_load_data',
                 'test_iter_return_type',
                 'test_dict_return_type',
                 'test_dict_json_return_type',
                 'test_tuple_return_type',
                 'test_tuple_json_return_type',
                 'test_set_return_type',
                 'test_set_json_return_type',
                 'test_table_return_type',
                 'test_table_json_return_type',
                 'test_callback_return_type',
                 'test_chunking',
                 'test_chunking_with_min',
                 'test_chunking_with_records',
                 'test_raw_sql',
                 'test_replace',
                 'test_replace_quote',
                 'test_placeholder_quote',
                 'test_big_replace',
                 'test_executemany',
                 'test_drop_table',
                 'test_disconnect']

        return unittest.TestSuite(map(TestMySQLHub, tests))

    def setUp(self):

        ####
        #TODO:
        #Most of the attribute initializations would be better placed
        #in __init__.  However, I get a doc string related error when
        #I try that from the base class, not sure why.  Skipping for now.
        ###
        self.test_data_rows = 0
        self.data_source = 'MySQL_test'
        self.db = 'test'
        self.table_name = 'DATA_SOURCES_TEST_DATA'
        self.callback_calls = 0
        self.limit = 100
        self.nsets = 986
        self.columns = set(['category', 'term', 'go_id', 'id', 'auto_pfamA'])

    def tearDown(self):
        sys.stdout.flush()

    def test_parse_data_sources(self):

        ##Instantiating base hub triggers data_sources.json parsing##
        bh = BaseHub()
        if self.data_source not in BaseHub.data_sources:
            msg = "The required data source, %s, was not found in %s" % (self.data_source, BaseHub.source_list_file)
            fail(msg)

    def test_db_existance(self):

        dh = MySQL(self.data_source)
        dbs = dh.get_databases()

        if 'test' not in dbs:
            msg = "No 'test' database found in %s.  To run this method create a 'test' db in %s." % (self.data_source, self.data_source)
            self.fail(msg)

    def test_execute_rules(self):

        rh = RDBSHub(self.data_source)

        ###
        #See RDBSHub.set_execute_rules for test descriptions
        ###

        #########
        #All tests should raise RDBSHubExecuteError
        #########

        # 1.) make sure we recognize all of the args, chicken being the exception here
        args = dict(chicken=1, proc='fake.proc', return_type='tuple')
        self.__try_it(rh, args)

        # 2.) proc or sql must be provided or we have nothing to execute
        args = dict(return_type='tuple', db=self.db)
        self.__try_it(rh, args)

        # 3.) placeholders and replace must be set to lists
        args = dict(placeholders=dict())
        self.__try_it(rh, args)
        args = dict(replace=dict())
        self.__try_it(rh, args)

        # 4.) key_column is required if the return type is dict, dict_json,
        # set, or set_json
        for key in rh.return_type_key_columns:
            args = dict(return_type=key, proc='fake.proc')
            self.__try_it(rh, args)

        # 5.) If a return type of callback is selected a callback key must be
        # provided wih a function reference
        args = dict(return_type='callback', proc='fake.proc')
        self.__try_it(rh, args)

        # 6.) chunk_size must be provided with a chunk_source
        args = dict(chunk_size=100, proc='fake.proc')
        self.__try_it(rh, args)
        args = dict(chunk_source='table.column', proc='fake.proc')
        self.__try_it(rh, args)

    def test_create_data_table(self):

        dh = MySQL(self.data_source)
        dh.execute(db=self.db,
                   proc="test.create_table")

        table_set = dh.execute(db=self.db,
                             proc="sql.ds_selects.get_tables",
                             key_column="Tables_in_test",
                             return_type="set")

        if self.table_name not in table_set:
            msg = "The table, %s, was not created in %s." % (self.table_name, self.db)
            self.fail(msg)

    def test_load_data(self):

        dh = MySQL(self.data_source)
        dh.use_database('test')

        ##Load Data##
        for row in TestMySQLHub.test_data:
            dh.execute(proc="test.insert_test_data",
                       placeholders=row)

        rowcount = dh.execute( db=self.db,
                            proc="sql.ds_selects.get_row_count",
                            replace=['auto_pfamA', self.table_name],
                            return_type='iter').get_column_data('rowcount')

        ##Confirm we loaded all of the rows##
        msg = 'Row count in data file, %i, does not match row count in db %i.' % (TestMySQLHub.test_data_rows, rowcount)
        self.assertEqual(rowcount, TestMySQLHub.test_data_rows, msg=msg)

    def test_table_iter(self):

        dh = MySQL(self.data_source)

        iter = dh.execute( db=self.db,
                           proc="test.get_data",
                           return_type='iter')

        msg = 'Row count in iter, %i, does not match row count in db %i.' % (iter.rowcount, TestMySQLHub.test_data_rows)
        self.assertEqual(iter.rowcount, TestMySQLHub.test_data_rows, msg=msg)

        rowcount = 0
        for data in iter:
            rowcount += 1

        msg = 'The iterations in iter, %i, do not match the row count in db %i.' % (rowcount, TestMySQLHub.test_data_rows)
        self.assertEqual(iter.rowcount, TestMySQLHub.test_data_rows, msg=msg)

    def test_iter_return_type(self):

        dh = MySQL(self.data_source)

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

        term = iter.get_column_data('term')
        if not term:
            msg = 'iter.get_column_data failed to retrieve `term` column.'
            fail(msg)

    def test_dict_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_dict_json_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_tuple_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_tuple_json_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_set_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_set_json_return_type(self):

        dh = MySQL(self.data_source)

        j = dh.execute( db=self.db,
                           proc="test.get_data",
                           limit=self.limit,
                           key_column='id',
                           return_type='set_json')

        data = json.loads(j)
        rowcount = len(data)

        msg = 'The items in data set, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def test_table_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_table_json_return_type(self):

        dh = MySQL(self.data_source)

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

    def test_callback_return_type(self):

        dh = MySQL(self.data_source)

        dh.execute( db=self.db,
                    proc="test.get_data",
                    callback=self.__callback_test,
                    limit=self.limit,
                    return_type='callback')

        msg = 'self.callback_calls, %i, does not match the row count %i.' % (self.callback_calls, self.limit)
        self.assertEqual(self.callback_calls, self.limit, msg=msg)

    def test_chunking(self):

        chunk_size = 10
        dh = MySQL(self.data_source)

        nsets = 0
        for d in  dh.execute( db=self.db,
                              proc="test.get_data",
                              chunk_size=10,
                              chunk_source='DATA_SOURCES_TEST_DATA.id'):

            nsets += 1

        msg = 'total chunk sets should be, %i, there were %i chunk sets found.' % (self.nsets, nsets)
        self.assertEqual(self.nsets, nsets, msg=msg)

    def test_chunking_with_min(self):

        chunk_size = 10
        dh = MySQL(self.data_source)

        nsets = 0
        for d in  dh.execute( db=self.db,
                              proc="test.get_data",
                              chunk_size=100,
                              chunk_min=5,
                              chunk_source='DATA_SOURCES_TEST_DATA.id'):

            nsets += 1

        msg = 'total chunk sets should be, %i, there were %i chunk sets found.' % (99, nsets)
        self.assertEqual(99, nsets, msg=msg)

    def test_chunking_with_records(self):

        chunk_size = 10
        dh = MySQL(self.data_source)

        nsets = 0
        for d in  dh.execute( db=self.db,
                              proc="test.get_data",
                              chunk_size=5,
                              chunk_total=50,
                              chunk_source='DATA_SOURCES_TEST_DATA.id'):

            nsets += 1

        msg = 'total chunk sets should be, %i, there were %i chunk sets found.' % (10, nsets)
        self.assertEqual(10, nsets, msg=msg)

    def test_raw_sql(self):

        sql = """SELECT `id`, `auto_pfamA`, `go_id`, `term`, `category`
                 FROM `test`.`DATA_SOURCES_TEST_DATA`"""

        dh = MySQL(self.data_source)

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

    def test_replace(self):

        rep_values = ['id',
                     'auto_pfamA',
                     'go_id',
                     'term',
                     'category',
                     'DATA_SOURCES_TEST_DATA']

        dh = MySQL(self.data_source)

        data = dh.execute( db=self.db,
                           proc="test.get_data_replace",
                           limit=self.limit,
                           replace=rep_values,
                           return_type='tuple')

        rowcount = len(data)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, self.limit)
        self.assertEqual(rowcount, self.limit, msg=msg)

    def test_replace_quote(self):

        rep_values = [ "GO:0015075",
                       "GO:0032934",
                       "GO:0003700",
                       "GO:0000795" ]

        dh = MySQL(self.data_source)

        data = dh.execute( db=self.db,
                           proc="test.get_replace_quote",
                           replace_quote=[rep_values],
                           return_type='tuple')

        rows = 90
        rowcount = len(data)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, rows)
        self.assertEqual(rowcount, rows, msg=msg)

    def test_placeholder_quote(self):

        p = [ "GO:0015075",
              "GO:0032934",
              "GO:0003700",
              "GO:0000795" ]

        dh = MySQL(self.data_source)

        data = dh.execute( db=self.db,
                           proc="test.get_placeholder_quote",
                           placeholders=p,
                           return_type='tuple')

        rows = 90
        rowcount = len(data)

        msg = 'The items in data tuple, %i, do not match the row count %i.' % (rowcount, rows)
        self.assertEqual(rowcount, rows, msg=msg)

    def test_big_replace(self):

        ids = [1,2,3,4,5,6,7,8,9,10]

        rep_values = ['id',
                     'auto_pfamA',
                     'go_id',
                     'term',
                     'category',
                     'DATA_SOURCES_TEST_DATA',
                     ids]

        dh = MySQL(self.data_source)

        data = dh.execute( db=self.db,
                           proc="test.get_big_replace",
                           limit=self.limit,
                           replace=rep_values,
                           return_type='tuple')

        rowcount = len(data)

    def test_executemany(self):

        dh = MySQL(self.data_source)
        dh.use_database('test')

        ##Load Data##
        placeholders = []
        for row in TestMySQLHub.test_data:
            placeholders.append( row )

        dh.execute(proc="test.insert_test_data",
                   executemany=True,
                   placeholders=placeholders)

        rowcount = dh.execute( db=self.db,
                            proc="sql.ds_selects.get_row_count",
                            replace=['auto_pfamA', self.table_name],
                            return_type='iter').get_column_data('rowcount')

        ##Confirm we loaded all of the rows##
        target_rowcount = 2*TestMySQLHub.test_data_rows
        msg = 'Row count in data file, %i, does not match row count in db %i.' % (target_rowcount, rowcount)
        self.assertEqual(rowcount, target_rowcount, msg=msg)

    def test_drop_table(self):

        dh = MySQL(self.data_source)

        dh.execute(db=self.db,
                   proc="test.drop_table")

        table_set = dh.execute(db=self.db,
                             proc="sql.ds_selects.get_tables",
                             key_column="Tables_in_test",
                             return_type="set")

        if self.table_name in table_set:
            msg = "The table, %s, was not dropped in %s." % (self.table_name, self.db)
            self.fail(msg)

    def test_disconnect(self):

        dh = MySQL(self.data_source)
        dh.disconnect()

    def __callback_test(self, row):
        self.callback_calls += 1

    def __try_it(self, rh, args):
        try:
            rh.set_execute_rules(args)
        except RDBSHubExecuteError, err:
            ##Yay! test worked
            pass
        else:
            ##OOh we should have an error here##
            self.fail("\tShould have raised RDBSHubExecuteError on args:%s" % (','.join(args.keys())))

def main():
    ##Load test data one time##
    TestMySQLHub.load_data()

    suite = TestMySQLHub.getSuite()
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    main()
