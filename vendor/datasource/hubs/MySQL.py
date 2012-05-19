import sys
import time
import re
from timeit import Timer

try:
    import simplejson as json
except ImportError:
    import json

import MySQLdb
import MySQLdb.cursors
import _mysql
from _mysql_exceptions import OperationalError

from datasource.bases.RDBSHub import RDBSHub, ChunkIterator, DataIterator, RDBSHubError

class MySQL(RDBSHub):
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
        __connection[ hostType ][ con_obj="Connection Object",
                                  cursor="Database cursor" ]
        """
        self.__connection = dict()

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

    ##########
    #Was thinking doing an explicit disconnect in a
    #destructor was a good idea but this leads to
    #an issue if the caller passes in a database cursor.  When a
    #database cursor is passed in we cannot call an explicit disconnect
    #and by having an explicit destructor the python gc does not do it's thing.
    #I think this could be a possible source of memory leakage but would need
    #to test more before coming to that conclusion.  For the moment
    #the MySQLdb module appears to automatically disconnect when
    #a MySQL object gets destroyed.  Something to watch out for.
    #########

    def __del__(self):
        self.disconnect()

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

    def escapeString(self, value):
        """
        Pass through to _mysql escapeString which calls mysql_escape_string().
        Would be better to call mysql_real_escape_string() since it takes the
        character set into account but it requires a connection object.  Connection
        objects are only created on query execution so we need to call it through
        the class.

        Parameters:
           value - The string to be escaped.
        """
        return _mysql.escape_string(value)

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
            self.__tryToConnect(hostType, db)

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
        host types found in __connection:

        Parameters:
           None

        Return:
           None
        """
        for hostType in self.__connection:
            if self.__connection[hostType]['cursor']:
                self.__connection[hostType]['cursor'].close()
                self.__connection[hostType]['cursor'] = None

            self.__connection[hostType]['con_obj'].commit()
            self.__connection[hostType]['con_obj'].close()


    """
    Private Methods
    """
    def __connect(self, hostType, db):

        ##Make sure we really need to connect##
        connect = False
        if hostType in self.__connection and self.__connection[hostType]['con_obj']:
            try:
                ##We have a connection, make sure it's active##
                self.__connection[hostType]['con_obj'].ping()
            except OperationalError:
                ##Connection is corrupt, reconnect##
                connect = True
        else:
            ##No connection for host type, make connection##
            connect = True

        if connect:
            ##No connection exists, connect##
            self.__connection[hostType] = dict( con_obj=None, cursor=None)

            if db:
                self.__connection[hostType]['con_obj'] = MySQLdb.connect( host=self.conf[hostType]['host'],
                                                                          user=self.conf[hostType]['user'],
                                                                          passwd=self.conf[hostType].get('passwd', ''),
                                                                          cursorclass=MySQLdb.cursors.DictCursor,
                                                                          db=db)
            else:
                self.__connection[hostType]['con_obj'] = MySQLdb.connect( host=self.conf[hostType]['host'],
                                                                          user=self.conf[hostType]['user'],
                                                                          passwd=self.conf[hostType].get('passwd', ''),
                                                                          cursorclass = MySQLdb.cursors.DictCursor)

            self.__connection[hostType]['cursor'] = self.__connection[hostType]['con_obj'].cursor()

    def __tryToConnect(self, hostType, db):

        for i in range(self.maxConnectAttempts):
            try:
                self.__connect(hostType, db)

                ##Let someone know this is not happening on the first try##
                if i > 0:
                    sys.stderr.write("\n%s: __tryToConnect succeeded on %i attempt. Database:%s" % (__name__, i, db))
                    sys.stderr.flush()
                ##We have a connection, move along##
                break

            except OperationalError, err:
                ##Connect failed, take a breather and then try again##
                sys.stderr.write("\n%s: __tryToConnect OperationalError encountered on attempt %i. Database:%s" % (__name__, i, db))
                sys.stderr.write("\nError detected was:\n%s\n" % (err))
                sys.stderr.flush()
                time.sleep(self.sleepInterval)
                continue

        if not self.__connection[hostType]['con_obj']:
            ###
            #If we made it here we've tried to connect maxConnectAttempts, it's time to throw
            #in the towel.  Clearly the universe is working against us today, chin up
            #tomorrow could be better.
            ###
            raise MySQLConnectError(self.maxConnectAttempts, self.dataSource)

    def __execute(self, sql, kwargs):

        db = kwargs['db']
        hostType = kwargs['host_type']
        cursor = None
        if self.clientCursor:
            cursor = self.clientCursor
        else:
            cursor = self.__connection[hostType]['cursor']

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
        self.__connection[hostType]['con_obj'].commit()

        return self.getData(cursor, kwargs)

    def __cursorExecute(self, sql, kwargs, cursor):
        if 'placeholders' in kwargs:
            cursor.execute(sql, kwargs['placeholders'])
        else:
            cursor.execute(sql)

class MySQLConnectError(RDBSHubError):

    def __init__(self, iterations, dataSource):
        self.iter = iterations
        self.dataSource = dataSource
    def __repr__(self):
        msg = "OperationalError encountered repeatedly while connecting.  Attempted to connect %i times to data source %s and failed... Feeling kindof sad right now :-(" % (self.iter, self.dataSource)
