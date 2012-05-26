import sys
import time
import re
from timeit import Timer

try:
    import simplejson as json
except ImportError:
    import json

from datasource.bases.RDBSHub import RDBSHub, ChunkIterator, DataIterator, RDBSHubError

class SQLHub(RDBSHub):
    """
    Derived RDBSHub class for MySQL.  Encapsulates sql execution and data retrieval.
    """

    def __init__(self, dataSource, **kwargs):

        ##Confirms required keys for datasource config info##
        RDBSHub.__init__(self, dataSource)

        ##These attributes are required for certain base class methods##
        self.dataSource = dataSource
        self.placeholderChar = '%s'

        self.quoteChar = """'"""
        self.maxConnectAttempts = 20
        self.sleepInterval = 1

        self.clientCursor = None
        if 'cursor' in kwargs:
            self.clientCursor = kwargs['cursor']

        ##Register return_type methods##
        self.validReturnTypes['iter'] = self.getIter
        self.validReturnTypes['dict'] = self.getDict
        self.validReturnTypes['dict_json'] = self.getDictJson
        self.validReturnTypes['tuple'] = self.getTuple
        self.validReturnTypes['tuple_json'] = self.getTupleJson
        self.validReturnTypes['set'] = self.getSet
        self.validReturnTypes['table'] = self.getTable
        self.validReturnTypes['table_json'] = self.getTableJson
        self.validReturnTypes['set_json'] = self.getSetJson
        self.validReturnTypes['callback'] = self.getCallback

        """
        SQLHub.connection[ hostType ][ con_obj="Connection Object",
                                  cursor="Database cursor" ]
        """
        SQLHub.connection = dict()

        ##Configuration object for data source instance##
        self.conf = self.getDataSourceConfig(self.dataSource)

        ##Load the procedures##
        self.loadProcs(self.dataSource)

        __all__ = ['getDatabases',
                   'useDatabase',
                   'escapeString',
                   'disconnect',
                   'execute',
                   'getIter',
                   'getDict',
                   'getDictJson',
                   'getList',
                   'getListJson',
                   'getSet',
                   'getSetJson',
                   'getCallback']

    def getDatabases(self):
        """
        Return a set of databases available for the datasource. The
        list is dynamically retrieved from the db instance specified
        in the datasource.

        Parameters:
           None

        Returns:
           Set of databases
        """
        ##Retrieve databases dynamically##
        dbs = self.execute(proc='sql.ds_selects.get_databases',
                           return_type='set',
                           key_column='Database')

        return dbs

    def useDatabase(self, db):
        """
        Selects the database to use.

        Parameters:
           db - Database name

        Returns:
           None
        """
        self.execute(proc='sql.ds_use.select_database',
                     replace=[db] )

    @RDBSHub.executeDecorator
    def execute(self, **kwargs):

        ##These values are populated by the base class executeDecorator
        hostType = kwargs['host_type']
        sql = kwargs['sql']
        db = kwargs['db']

        ##########
        #sqlChunks is a list of sql statements to execute.  It's built
        #by the base class when a caller requests chunking.
        ##########
        sqlChunks = kwargs['sql_chunks']

        args = False
        if 'args' in kwargs:
            args = kwargs['args']

        if not self.clientCursor:
            self.tryToConnect(hostType, db)

        if len(sqlChunks) > 0:
            return ChunkIterator(sqlChunks, kwargs, self.__execute)

        return self.__execute(sql, kwargs)

    def getIter(self, cursor, kwargs):
        return DataIterator(cursor.fetchall(), cursor.description, cursor.rowcount)

    def getDict(self, cursor, kwargs):

        rowsDict = dict()
        keyColumn = kwargs['key_column']

        while(1):
            row = cursor.fetchone()
            #All done
            if row == None:
                break

            if keyColumn in row:
                rowsDict[ row[keyColumn] ] = row
            else:
                msg = "The key_column provided, %s, does not match any of the available keys %s"%(keyColumn, ','.join(row.keys))
                raise RDBSHubError(msg)

        return rowsDict

    def getDictJson(self, cursor, kwargs):
        rowsDict = self.getDict(cursor, kwargs)
        return json.dumps(rowsDict)

    def getTuple(self, cursor, kwargs):
        return cursor.fetchall()

    def getTupleJson(self, cursor, kwargs):
        rows = self.getTuple(cursor, kwargs)
        return json.dumps(rows)

    def getSet(self, cursor, kwargs):

        dbSet = set()
        keyColumn = kwargs['key_column']

        while(1):
            row = cursor.fetchone()
            #All done
            if row == None:
                break
            if keyColumn in row:
                dbSet.add(row[keyColumn])
            else:
                msg = "The key_column provided, %s, does not match any of the available keys %s"%(keyColumn, ','.join(row.keys))
                raise RDBSHubError(msg)

        return dbSet

    def getSetJson(self, cursor, kwargs):
        ##Sets are not serializable into json, build a dict with None for each key##
        rowsDict = dict()
        keyColumn = kwargs['key_column']
        while(1):
            row = cursor.fetchone()
            #All done
            if row == None:
                break
            if keyColumn in row:
                rowsDict[row[keyColumn]] = None
            else:
                msg = "The key_column provided, %s, does not match any of the available keys %s"%(keyColumn, ','.join(row.keys))
                raise RDBSHubError(msg)

        return json.dumps(rowsDict)

    def getTable(self, cursor, kwargs):

        ##Get ordered list of column names##
        cols = []
        for row in cursor.description:
            cols.append( row[0] )
        data = cursor.fetchall()

        return { 'columns':cols, 'data':data }

    def getTableJson(self, cursor, kwargs):
        dataStruct = self.getTable(cursor, kwargs)
        return json.dumps(dataStruct)

    def getCallback(self, cursor, kwargs):
        callback = kwargs['callback']
        if cursor.rowcount > 0:
            while(1):
                row = cursor.fetchone()
                #All done
                if row == None:
                    break
                callback(row)

    def disconnect(self):
        """
        Close the db cursor and commit/close the connection object for all
        host types found in SQLHub.connection:

        Parameters:
           None

        Return:
           None
        """
        for hostType in SQLHub.connection:
            if SQLHub.connection[hostType]['cursor']:
                SQLHub.connection[hostType]['cursor'].close()

            if SQLHub.connection[hostType]['con_obj'].open:
                SQLHub.connection[hostType]['con_obj'].commit()
                SQLHub.connection[hostType]['con_obj'].close()


    """
    Private Methods
    """
    def connect(self, hostType, db):
        raise NotImplemented

    def tryToConnect(self, hostType, db):
        raise NotImplemented

    def __execute(self, sql, kwargs):

        db = kwargs['db']
        hostType = kwargs['host_type']
        cursor = None
        if self.clientCursor:
            cursor = self.clientCursor
        else:
            cursor = SQLHub.connection[hostType]['cursor']

        ##Get the proc name for debug message##
        proc = ""
        if 'proc' in kwargs:
            proc = kwargs['proc']

        ##Caller requests no sql execution##
        if 'debug_noex' in kwargs:
            self.showDebug(db,
                           self.conf[hostType]['host'],
                           hostType,
                           proc,
                           sql,
                           None)
            return []

        ##Caller wants to sql execution time##
        if 'debug_show' in kwargs:

            def timewrapper():
                self.__cursorExecute(sql, kwargs, cursor)

            t = Timer(timewrapper)
            tmsg = ""
            try:
                tmsg = t.timeit(1)
            except:
                t.print_exc()

            self.showDebug(db,
                           self.conf[hostType]['host'],
                           hostType,
                           proc,
                           sql,
                           tmsg)
        else:
            self.__cursorExecute(sql, kwargs, cursor)

        ##Commit transaction##
        SQLHub.connection[hostType]['con_obj'].commit()

        return self.getData(cursor, kwargs)

    def __cursorExecute(self, sql, kwargs, cursor):
        if 'placeholders' in kwargs:
            cursor.execute(sql, kwargs['placeholders'])
        else:
            cursor.execute(sql)
