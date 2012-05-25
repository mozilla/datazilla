import sys
import time

import MySQLdb
import MySQLdb.cursors

import _mysql
from _mysql_exceptions import OperationalError

from datasource.bases.RDBSHub import RDBSHubError
from datasource.bases.SQLHub import SQLHub

class MySQL(SQLHub):
    """
    Derived RDBSHub class for MySQL.  Encapsulates sql execution and data retrieval.
    """

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

    """
    Private Methods
    """
    def connect(self, hostType, db):

        ##Make sure we really need to connect##
        connect = False
        if hostType in SQLHub.connection and SQLHub.connection[hostType]['con_obj']:
            try:
                ##We have a connection, make sure it's active##
                SQLHub.connection[hostType]['con_obj'].ping()
            except OperationalError:
                ##Connection is corrupt, reconnect##
                connect = True
        else:
            ##No connection for host type, make connection##
            connect = True

        if connect:
            ##No connection exists, connect##
            SQLHub.connection[hostType] = dict( con_obj=None, cursor=None)

            if db:
                SQLHub.connection[hostType]['con_obj'] = MySQLdb.connect( host=self.conf[hostType]['host'],
                                                                          user=self.conf[hostType]['user'],
                                                                          passwd=self.conf[hostType].get('passwd', ''),
                                                                          cursorclass=MySQLdb.cursors.DictCursor,
                                                                          db=db)
            else:
                SQLHub.connection[hostType]['con_obj'] = MySQLdb.connect( host=self.conf[hostType]['host'],
                                                                          user=self.conf[hostType]['user'],
                                                                          passwd=self.conf[hostType].get('passwd', ''),
                                                                          cursorclass = MySQLdb.cursors.DictCursor)

            SQLHub.connection[hostType]['cursor'] = SQLHub.connection[hostType]['con_obj'].cursor()


    def tryToConnect(self, hostType, db):

        for i in range(self.maxConnectAttempts):
            try:
                self.connect(hostType, db)

                ##Let someone know this is not happening on the first try##
                if i > 0:
                    sys.stderr.write("\n%s: tryToConnect succeeded on %i attempt. Database:%s" % (__name__, i, db))
                    sys.stderr.flush()
                ##We have a connection, move along##
                break

            except OperationalError, err:
                ##Connect failed, take a breather and then try again##
                sys.stderr.write("\n%s: tryToConnect OperationalError encountered on attempt %i. Database:%s" % (__name__, i, db))
                sys.stderr.write("\nError detected was:\n%s\n" % (err))
                sys.stderr.flush()
                time.sleep(self.sleepInterval)
                continue

        if not SQLHub.connection[hostType]['con_obj']:
            ###
            #If we made it here we've tried to connect maxConnectAttempts, it's time to throw
            #in the towel.  Clearly the universe is working against us today, chin up
            #tomorrow could be better.
            ###
            raise MySQLConnectError(self.maxConnectAttempts, self.dataSource)


class MySQLConnectError(RDBSHubError):

    def __init__(self, iterations, dataSource):
        self.iter = iterations
        self.dataSource = dataSource
    def __repr__(self):
        msg = "OperationalError encountered repeatedly while connecting.  Attempted to connect %i times to data source %s and failed... Feeling kindof sad right now :-(" % (self.iter, self.dataSource)
