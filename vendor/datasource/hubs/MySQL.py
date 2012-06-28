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

    def escape_string(self, value):
        """
        Pass through to _mysql escape_string which calls mysql_escape_string().
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
    def connect(self, host_type, db):

        ##Make sure we really need to connect##
        connect = False
        if host_type in self.connection and self.connection[host_type]['con_obj']:
            try:
                ##We have a connection, make sure it's active##
                self.connection[host_type]['con_obj'].ping()
            except OperationalError:
                ##Connection is corrupt, reconnect##
                connect = True
        else:
            ##No connection for host type, make connection##
            connect = True

        if connect:
            ##No connection exists, connect##
            self.connection[host_type] = dict( con_obj=None, cursor=None)

            if db:
                self.connection[host_type]['con_obj'] = MySQLdb.connect( host=self.conf[host_type]['host'],
                                                                          user=self.conf[host_type]['user'],
                                                                          passwd=self.conf[host_type].get('passwd', ''),
                                                                          charset="utf8",
                                                                          cursorclass=MySQLdb.cursors.DictCursor,
                                                                          db=db)
            else:
                self.connection[host_type]['con_obj'] = MySQLdb.connect( host=self.conf[host_type]['host'],
                                                                          user=self.conf[host_type]['user'],
                                                                          passwd=self.conf[host_type].get('passwd', ''),
                                                                          charset="utf8",
                                                                          cursorclass = MySQLdb.cursors.DictCursor)

            self.connection[host_type]['con_obj'].autocommit(False)
            self.connection[host_type]['cursor'] = self.connection[host_type]['con_obj'].cursor()

    def try_to_connect(self, host_type, db):

        for i in range(self.max_connect_attempts):
            try:
                self.connect(host_type, db)

                ##Let someone know this is not happening on the first try##
                if i > 0:
                    sys.stderr.write("\n%s: try_to_connect succeeded on %i attempt. Database:%s" % (__name__, i, db))
                    sys.stderr.flush()
                ##We have a connection, move along##
                break

            except OperationalError, err:
                ##Connect failed, take a breather and then try again##
                sys.stderr.write("\n%s: try_to_connect OperationalError encountered on attempt %i. Database:%s" % (__name__, i, db))
                sys.stderr.write("\nError detected was:\n%s\n" % (err))
                sys.stderr.flush()
                time.sleep(self.sleep_interval)
                continue

        if not self.connection[host_type]['con_obj']:
            ###
            #If we made it here we've tried to connect max_connect_attempts, it's time to throw
            #in the towel.  Clearly the universe is working against us today, chin up
            #tomorrow could be better.
            ###
            raise MySQLConnectError(self.max_connect_attempts, self.data_source)


class MySQLConnectError(RDBSHubError):

    def __init__(self, iterations, data_source):
        self.iter = iterations
        self.data_source = data_source
    def __repr__(self):
        msg = "OperationalError encountered repeatedly while connecting.  Attempted to connect %i times to data source %s and failed... Feeling kindof sad right now :-(" % (self.iter, self.data_source)
