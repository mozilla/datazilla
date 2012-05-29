"""
This software is licensed under the [Mozilla Tri-License][MPL]:

***** BEGIN LICENSE BLOCK *****
Version: MPL 1.1/GPL 2.0/LGPL 2.1

The contents of this file are subject to the Mozilla Public License Version
1.1 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at
http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
for the specific language governing rights and limitations under the
License.

The Original Code is DataSouces.

The Initial Developer of the Original Code is
Jonathan Eads (Jeads).
Portions created by the Initial Developer are Copyright (C) 2011
the Initial Developer. All Rights Reserved.

Contributor(s):
   Jonathan Eads <superjeads AT gmail DOT org>

Alternatively, the contents of this file may be used under the terms of
either the GNU General Public License Version 2 or later (the "GPL"), or
the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
in which case the provisions of the GPL or the LGPL are applicable instead
of those above. If you wish to allow use of your version of this file only
under the terms of either the GPL or the LGPL, and not to allow others to
use your version of this file under the terms of the MPL, indicate your
decision by deleting the provisions above and replace them with the notice
and other provisions required by the GPL or the LGPL. If you do not delete
the provisions above, a recipient may use your version of this file under
the terms of any one of the MPL, the GPL or the LGPL.

***** END LICENSE BLOCK *****
"""
import sys
import math
import re

import sys
from datasource.bases.BaseHub import BaseHub, DataHubError

class RDBSHub(BaseHub):
    """
    Base class for all relational database hubs.
    """

    @staticmethod
    def executeDecorator(func):
        """
        Function decorator for execute().  Initializes wrapper
        function that checks the execute rules against the kwargs
        provided by caller and sets values for sql, host_type, db,
        and sql_chunks.  The execute function in all derived RDBSHub's
        should use the executeDecorator.

           Parameters:
              func - function ref

           Returns:
              wrapped function ref
        """
        def wrapper(self, **kwargs):
            self.setExecuteRules(kwargs)
            self.getExecuteData(self.dataSource, kwargs)
            return func(self, **kwargs)

        return wrapper

    def __init__(self, dataSourceName):
        """
        A derived class of BaseHub, serves as a base class for any Relational
        Database hubs.
        """
        BaseHub.__init__(self)

        ##allowed keys in execute##
        self.executeKeys = set(['db',
                              'proc',
                              'sql',
                              'host_type',
                              'placeholders',
                              'replace',
                              'replace_quote',
                              'limit',
                              'offset',
                              'chunk_size',
                              'chunk_source',
                              'chunk_min',
                              'return_type',
                              'key_column',
                              'callback',
                              'debug_show',
                              'debug_noex' ])

        ##Default values for execute kwargs##
        self.defaultHostType = 'master_host'
        self.defaultReturnType = 'tuple'

        ##replace string base for replace functionality in execute##
        self.replaceString = 'REP'

        #####
        #set of return types that require a key_column
        #####
        self.returnTypeKeyColumns = set(['dict', 'dict_json', 'set', 'set_json'])

        #####
        #One of these keys must be provided to execute
        #####
        self.executeRequiredKeys = set(['proc', 'sql'])

        ###
        #This data structure is used to map the return_type provided to
        #execute() to the derived hub method.  Derived hub's have to map
        #their methods by setting the appropriate function reference to
        #its associated key in validReturnTypes.
        ###
        self.validReturnTypes = { 'iter':None,
                                  'dict':None,
                                  'dict_json':None,
                                  'tuple':None,
                                  'tuple_json':None,
                                  'set':None,
                                  'set_json':None,
                                  'table':None,
                                  'table_json':None,
                                  'callback':None }

        ##Dictionary of required keys for RDBS datasources##
        self.dataSourceReqKeys = dict(
                           #required keys
                           req=set(['hub', 'master_host']),
                           #optional keys but if present have additional key requirements
                           databases=set(['name', 'procs']),
                           master_host=set(['host', 'user']),
                           read_host=set(['host', 'user']),
                           dev_host=set(['host', 'user']) )

        ###
        #List of SQL tokens that must follow a WHERE statement
        ###
        self.postWhereTokens = ['GROUP BY','HAVING','ORDER BY','LIMIT','OFFSET','PROCEDURE','INTO','FOR UPDATE']

        ####
        #Validate the information in dataSources is complete
        #so we can provide the caller with useful messaging
        #regarding what is missing when a class is instantiated.
        ####
        self.validateDataSource(dataSourceName)

        self.prettySqlRegex = re.compile('\s+', re.DOTALL)

        self.defaultPlaceholder = '?'

        __all__ = ['loadProcs',
                   'getProc',
                   'getData',
                   'validateDataSource',
                   'setExecuteRules',
                   'getExecuteData']

    """
    Public Interface
    """
    def loadProcs(self, dataSource):
        BaseHub.loadProcs(dataSource)

    def getProc(self, dataSource, proc):
        """
        Pass through to the BaseHub.getProc() method.

        Parameters:
           dataSource - data source to retrive proc from
           proc - full proc path ex: mysql.selects.get_stuff

        Returns:
           proc datastructure from the data source
        """
        return BaseHub.getProc(dataSource, proc)

    def getData(self, cursor, kwargs):
        """
        Executes the appropriate derived class getData function associated
        with the return type.  Derived classes register getData functions
        in self.validReturnTypes[ return_type ] = getDataFunctionRef.

        Parameters:
           cursor - db cursor reference
           kwargs - argument dictionary to pass to the derived class execute

        Returns:
           return value of derived class getData function
        """
        if 'return_type' in kwargs:
            returnType = kwargs['return_type']
            if returnType not in self.validReturnTypes:
                msg = 'The return_type value %s is not recognized. Possible values include [%s].'%(returnType, ','.join(self.validReturnTypes.keys()))
                raise RDBSHubExecuteError(msg)

            if not self.validReturnTypes[returnType]:
                ##Derived class has not mapped a function ref to the return type##
                msg = 'The derived hub, %s, has not mapped a function to %s in self.validReturnTypes.'%(self.__class__.__name__, returnType)
                raise RDBSHubExecuteError(msg)

            returnValue = self.validReturnTypes[returnType](cursor, kwargs)
            return returnValue

        else:
            ##Return type not provided##
            msg = 'The return_type key was not provided.  Add key:"return_type" value: [%s] to kwargs.'%(','.join(self.validReturnTypes.keys()))
            raise RDBSHubError(msg)

    def validateDataSource(self, dataSourceName):
        """
        Iterates through dataSourceReqKeys and confirms required
        key/value pairs.  Probably a better way of doing this but
        not thinking of anything more elegent at the moment.  Attempting
        to provide the caller with clear messaging regarding missing fields
        in the data source file.

        Parameters:
           dataSourceName - name of the datasource to test

        Returns:
           None
        """
        for key in self.dataSourceReqKeys:
            if key is 'req':
                msg = 'the %s source object in %s' % (dataSourceName, BaseHub.sourceListFile)
                ##Confirm required keys##
                BaseHub.checkKeys(self.dataSourceReqKeys[key], BaseHub.dataSources[dataSourceName], True, msg)
            elif key is 'databases':

                if key in BaseHub.dataSources[dataSourceName]:
                    for i in range(len(BaseHub.dataSources[dataSourceName][key])):
                        db = BaseHub.dataSources[dataSourceName][key][i]
                        msg = 'the %s.%s index position %i in %s' % (dataSourceName, key, i, BaseHub.sourceListFile)
                        BaseHub.checkKeys(self.dataSourceReqKeys[key], db, True, msg)
            else:
                msg = 'the %s.%s in %s' % (dataSourceName, key, BaseHub.sourceListFile)
                if key in BaseHub.dataSources[dataSourceName]:
                    BaseHub.checkKeys(self.dataSourceReqKeys[key], BaseHub.dataSources[dataSourceName][key], True, msg)

    def setExecuteRules(self, kwargs):
        """
        Implement the ruleset associated with the arguments to execute.  If a rule
        fails raise RDBSHubExecuteError.  The entire api to execute() is driven by
        key/value pairs which makes me cringe a bit.  However this provides a very
        convenient command line interface and hopefully it's easy to remember so
        i'm sticking with it.  Compensating for the approach with some explicit
        rules that the base class manages.  We want to make sure the caller gets
        clear messaging on argument requirements.

        Parameters:
           kwargs - kwargs passed to execute

        Returns:
           None
        """
        ####
        #Set default return_type here so we
        #can test for valid return types
        ####
        kwargs.setdefault('return_type', self.defaultReturnType)

        ###
        #Converting kwargs.keys to a set so
        #we can use snappy set operations, trying
        #to cut down on the number of conditional statements
        ###
        kwargsSet = set(kwargs.keys())

        #########
        #This kinda sucks and won't scale...
        #I can think of some cleaner solutions using classes or functions
        #but trying to keep overhead as light as possible for rule
        #implementation.  If a lot more rules get added fancy might
        #be the way to go here.
        ########

        ###
        # make sure we recognize all of the kwargs
        ###
        if not kwargsSet <= self.executeKeys:
            ##Caller has provided keys not in executeKeys, get the difference##
            d = kwargsSet - self.executeKeys
            raise RDBSHubExecuteError("The following keys, %s, are not recognized by execute()" % (','.join(d)))

        ###
        #  proc or sql must be provided or we have nothing to execute
        ###
        #If we don't have intersection none of the required keys are present##
        if not self.executeRequiredKeys & kwargsSet:
            raise RDBSHubExecuteError("The proc or sql argument must be provided to execute()")

        ###
        # placeholders and replace must be set to lists
        ###
        if ('placeholders' in kwargsSet) and (type(kwargs['placeholders']) is not list):
            raise RDBSHubExecuteError("The value of the placeholders argument must be a list.")
        if ('replace' in kwargsSet) and (type(kwargs['replace']) is not list):
            raise RDBSHubExecuteError("The value of the replace argument must be a list.")
        ###
        # key_column is required if the return type is dict, dict_json,
        # set, or set_json
        ###
        if (kwargs['return_type'] in self.returnTypeKeyColumns) and ('key_column' not in kwargsSet):
            ##No keyColumns found in kwargsSet##
            raise RDBSHubExecuteError("return types of %s require the key_column argument" % ','.join(self.returnTypeKeyColumns))

        ###
        # If a return type of callback is selected a callback key must be
        # provided wih a function reference
        ###
        if (kwargs['return_type'] == 'callback') and ('callback' not in kwargsSet):
            raise RDBSHubExecuteError("the callback return type requires the callback argument")

        ###
        # chunk_size must be provided with a chunk_source
        ###
        if ('chunk_size' in kwargsSet) and ('chunk_source' not in kwargsSet):
            raise RDBSHubExecuteError("when a chunk size is provided the chunk_source argument must be provided")
        if ('chunk_source' in kwargsSet) and ('chunk_size' not in kwargsSet):
            raise RDBSHubExecuteError("when a chunk column is provided the chunk_size argument must be provided")

    def getExecuteData(self, dataSource, kwargs):

        ##Al of these values are loaded in kwargs##
        db = ""
        sqlStruct = None
        hostType = ""
        sql = ""
        sqlChunks = []

        ##Set sql##
        if 'proc' in kwargs:
            sqlStruct = self.getProc(dataSource, kwargs['proc'])
            sql = sqlStruct['sql']
            ##If a host type is found in the proc file use it
            if 'host_type' in sqlStruct:
                hostType = sqlStruct['host_type']
        elif 'sql' in kwargs:
            sql = kwargs['sql']

        ##Set hostType##
        if 'host_type' in kwargs:
            ####
            #If the caller provides a host_type, override one
            #found in the proc file
            ####
            hostType = kwargs['host_type']
        elif not hostType:
            ##No host type in proc file or in kwargs, set default
            hostType = self.defaultHostType

        ##Set db##
        if 'db' in kwargs:
            db = kwargs['db']
        elif 'default_db' in self.conf:
            db = self.conf['default_db']
            kwargs['db'] = db
        #####
        #If we make it here and db is still not set, caller could be
        #using explicit database names in their SQL.  If their not
        #we will get an error from the RDBS
        #####

        if 'placeholders' in kwargs:
            ##Set DB interface placeholder char##
            sql = sql.replace(self.defaultPlaceholder, self.placeholderChar)

        ##Make replacements in sql##
        key = ""
        quote = False
        if 'replace' in kwargs:
            key = 'replace'
        elif 'replace_quote' in kwargs:
            key = 'replace_quote'
            quote = True
        if key:
            sql = self.__replaceSql(sql, key, kwargs, quote)

        ##Set limits and offset##
        if 'limit' in kwargs:
            sql = "%s LIMIT %s" % (sql, str(kwargs['limit']))
        if 'offset' in kwargs:
            sql = "%s OFFSET %s" % (sql, str(kwargs['limit']))

        ####
        #Compute number of execute sets if user requests chunking
        #ORDER IS CRITICAL HERE: sql must be passed to chunk stuff
        #after all alterations are made to it.
        ####
        if ('chunk_size' in kwargs) and ('chunk_source' in kwargs):
            sqlChunks = self.__getExecuteSets(sql, kwargs)

        ##Load data for execute##
        kwargs['sql'] = sql
        kwargs['host_type'] = hostType
        kwargs['db'] = db
        kwargs['sql_chunks'] = sqlChunks

    def showDebug(self, db, host, hostType, proc, sql, tmsg):
        """
        Writes debug message to stdout.

        Parameters:
           db - name of database that query is executed against
           host - host name the database resides on.
           hostType - type of host ex: master_host, read_host, or dev_host
           proc - full path to proc
           tmsg - execution time

        Returns:
           None
        """
        msg = ""

        sql = self.prettySqlRegex.sub(" ", sql)
        if tmsg:
            msg = "%s debug message:\n\thost:%s db:%s host_type:%s proc:%s\n\tExecuting SQL:%s\n\tExecution Time:%.4e sec\n\n"\
                  %(self.__class__, host, db, hostType, proc, sql, tmsg)
        else:
            msg = "%s debug message:\n\thost:%s db:%s host_type:%s proc:%s\n\tExecuting SQL:%s\n\n"\
                  %(self.__class__, host, db, hostType, proc, sql)

        sys.stdout.write(msg)
        sys.stdout.flush()

    def escapeString(self, value):
        # Should be implemented in the subclass
        raise NotImplemented()

    ######
    #Private methods
    ######
    def __replaceSql(self, sql, key, kwargs, quote):
        for i in range(len(kwargs[key])):
            r = kwargs[key][i]
            if quote:

                if type(r) == type([]):
                    joinChar = "%s,%s"%(self.quoteChar,self.quoteChar)
                    ###
                    #r could contain integers which will break join
                    #make sure we cast to strings
                    ###
                    r = joinChar.join( map(lambda s: self.escapeString(str(s)), r) )

                sql = sql.replace("%s%i"%(self.replaceString, i), "%s%s%s"%(self.quoteChar, r, self.quoteChar))

            else:

                if type(r) == type([]):
                    ###
                    #r could contain integers which will break join
                    #make sure we cast to strings
                    ###
                    r = ",".join(map(str, r))

                sql = sql.replace("%s%i"%(self.replaceString, i), r)

        ####
        #If any replace failed, make sure we get rid of all of
        #the REP strings
        ####
        sql = re.sub( '%s%s' % (self.replaceString, '\d+'), '', sql)

        return sql

    def __getExecuteSets(self, sql, kwargs):

        table, column = kwargs['chunk_source'].split('.')
        chunkSize = int(kwargs['chunk_size'])

        chunkStart = 0
        if 'chunk_min' in kwargs:
            chunkStart = int(kwargs['chunk_min'])

        if not (table and column and chunkSize):
            msg = "chunk_source must be set to explicit column name that includes the table. Example: table_name.column_name"
            raise RDBSHubError(msg)

        max = self.execute( db=kwargs['db'],
                            proc='sql.ds_selects.get_max',
                            replace=[ column, table ],
                            return_type='iter')

        minId = 0
        if 'chunk_min' in kwargs:
            minId = int( kwargs['chunk_min'] ) 
        else:
            min = self.execute( db=kwargs['db'],
                                proc='sql.ds_selects.get_min',
                                replace=[ column, table ],
                                return_type='iter')
            minId = int(min.getColumnData('min_id'))

        maxId = int(max.getColumnData('max_id') or 0)

        ##Total rows##
        nRows = (maxId - minId + 1)
        ##Total sets##
        nSets = int(math.ceil(float(nRows)/float(chunkSize)))

        ##Load table and column for execute##
        kwargs['chunk_table'] = table
        kwargs['chunk_column'] = column

        ##Get all the set id chunks for execute##
        sqlChunks = []
        for setNum in range(nSets):
            idSet = range(minId+setNum*chunkSize, minId+(setNum+1)*chunkSize)
            setSql = self.__buildSetWhere(idSet, sql, kwargs)
            sqlChunks.append(setSql)

        return sqlChunks

    def __buildSetWhere(self, idSet, sql, kwargs):

        #####
        #Build the WHERE IN clause for chunk set
        #####
        t = kwargs['chunk_table']
        c = kwargs['chunk_column']

        whereInSql = '(%s IN (%s))' % (c, ','.join(map(str, idSet)))

        whereIndex = sql.find('WHERE')

        if whereIndex > 0:
            ####
            #Statement already has a WHERE clause, append just the IN (list) bit
            ####
            sql = '%s %s AND %s' % (sql[0:(whereIndex+5)],whereInSql,sql[(whereIndex+6):])
            return sql
        else:
            ####
            #We don't have a WHERE clause, check for postWhereTokens to place
            #the WHERE clause before
            ####
            for token in self.postWhereTokens:
                tokenIndex = sql.find(token)
                if tokenIndex > 0:
                    sql = '%s WHERE %s %s' % (sql[0:(tokenIndex-1)],whereInSql,sql[tokenIndex:])
                    return sql

        ######
        #If we make it to here the sql has no pre-existing
        #WHERE and no postWhereTokens, we can append safely
        ######
        sql += ' WHERE %s'%(whereInSql)

        return sql

class ChunkIterator:

    def __init__(self, sqlChunks, kwargs, executeRef):

        self.sqlChunks = sqlChunks
        self.kwargs = kwargs
        self.chunks = len(sqlChunks)
        self.chunkIndex = 0
        self.executeRef = executeRef

    def __iter__(self):
        return self

    def next(self):

        try:
            sql = self.sqlChunks[ self.chunkIndex ]
            self.chunkIndex += 1
            return self.executeRef(sql, self.kwargs)

        except IndexError:
            ##Reset iterator##
            self.chunkIndex = 0
            raise StopIteration

class DataIterator:

    def __init__(self, data, desc, rowcount):

        self.data = data
        self.description = desc
        self.rowcount = rowcount
        self.rowIndex = 0

    def __iter__(self):
        return self

    def getColumnData(self, columnName):

        try:
            return self.data[0][columnName]

        except IndexError:
            ##Either no column match, or no data##
            return None

    def next(self):
        try:
            row = self.data[ self.rowIndex ]
            self.rowIndex += 1
            return row

        except IndexError:
            ##Reset iterator##
            self.rowIndex = 0
            raise StopIteration

class RDBSHubError(DataHubError):
    """Base class for all RDBSHub derived class errors.  Takes an error message and returns string representation in __repr__."""
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return self.msg

class RDBSHubExecuteError(DataHubError):
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return self.msg
