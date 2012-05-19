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
import os

try:
    import simplejson as json
except ImportError:
    import json

import pprint
import re

class BaseHub:
    """
    A base class for all derived data hub classes.
    """
    ##CLASS ATTRIBUTES##

    #Regex for removing python style comments, newlines, and tabs from a multiline string
    commentRegex = re.compile('\"\"\".*?\"\"\"|\#.*?\n|\n|\t', re.DOTALL)

    #Data structure holding all data sources
    dataSources = dict()

    #data structure mapping data sources to associated procedures
    procs = dict( sql=dict() )

    #Full path to data source json file
    sourceListFile = ''

    #Name of environment variable pointing to the data source json file
    dataSourceEnv = 'DATASOURCES'

    defaultDataSourceFile = 'data_sources.json'

    #Directory containing procs for unit tests and general sql
    defaultProcDir = 'procs'

    ##List of all built in proc files##
    builtInProcs = []

    ##END CLASS ATTRIBUTES##

    def __init__(self):
        ##Public Interface Methods##
        __all__ = ['getDataSourceConfig']

    """
    Static Methods
    """
    @staticmethod
    def getSources(sourceFilePath, defaultSource):
        """
        Staticmethod that loads list of data sources from a json file.

           Parameters: None

           Returns: None
        """
        sourceFileObj = open(sourceFilePath)

        sourceFile = None
        try:
            sourceFile = sourceFileObj.read()
        finally:
            sourceFileObj.close()

        dataSources = BaseHub.deserializeJson(sourceFile)

        if defaultSource:
            ##Load the procs##
            for d in dataSources:
                ####
                #Might eventually need a way to load these for specific
                #sources.  This approach loads all procs into all sources
                #but it will suffice for now...
                ####
                dataSources[d].update( { BaseHub.defaultProcDir:BaseHub.builtInProcs } )

        BaseHub.addDataSource(dataSources)

    @staticmethod
    def deserializeJson(sourceFile):
        """
        Staticmethod for deserializing json with python style comments in it.

           Parameters:
              sourceFile - Multi line string containing json to deserialize.  Can
                           contain python style comments that will be removed before
                           before deserialization.

              Returns:
                 python object without comments
        """
        return json.loads(BaseHub.stripPythonComments(sourceFile))

    @staticmethod
    def stripPythonComments(dataString):
        """
        Staticmethod that strips python style comments out of a string

           Parameters:
              dataString - Multiline string with python style comments

           Returns:
              python string with comments removed
        """
        return BaseHub.commentRegex.sub(" ", dataString)

    @staticmethod
    def checkKeys(reqKeys, dictTarget, defined=False, sourceName=""):
        """
        Staticmethod that checks keys and values in dictionary.  Raises
        DataSourceKeyError if a required key or value is not defined.
        The main usage of checkKeys is when we need to let the caller know
        something is missing from a critical file like data_sources.json
        or an associated procedure file.

        Parameters:
           reqKeys - A list of required keys.
           dictTarget - Dictionary to test against.
           defined - Boolean, defaults to undefined.  If true the key values are
                     required to be defined.
           sourceName - Defaults to the str representation of the dictTarget. Caller
                        can set this to any str.  For instance if the structure being
                        tested is loaded from a file, using the file name as the sourceName
                        is a good hint for the caller.

        Returns:
           None
        """
        missingKeys = []
        valuesNotDefined = []

        for key in reqKeys:
            if key not in dictTarget:
                missingKeys.append(key)
            else:
                if defined:
                    if not dictTarget[key]:
                        valuesNotDefined.append(key)

        msg = ""
        mLen = 0
        ##Caller requires keys only##
        if missingKeys:
            ##Set source name to dictTarget variable name##
            if not sourceName:
                pp = pprint.PrettyPrinter(indent=3)
                sourceName = pp.pformat(dictTarget)

            mLen = len(missingKeys)
            if mLen > 1:
                msg = 'The required keys: [%s] were not found in\n%s' % (','.join(missingKeys), sourceName)
            else:
                msg = 'The required key, %s, was not found in\n%s' % (','.join(missingKeys), sourceName)

            raise DataSourceKeyError(msg)

        ##Caller requires key values to be defined##
        if valuesNotDefined:
            ##Set source name to dictTarget variable name##
            if not sourceName:
                pp = pprint.PrettyPrinter(indent=4)
                sourceName = pp.pformat(dictTarget)

            mLen = len(valuesNotDefined)
            if mLen > 1:
                msg = 'The following keys do not have values: [%s] in\n%s' % (','.join(valuesNotDefined), sourceName)
            else:
                msg = 'The following key, %s, does not have a value in\n%s' % (','.join(valuesNotDefined), sourceName)

            raise DataSourceError(msg)

    @staticmethod
    def loadProcs(dataSource):
        """
        Loads procedure json files specified in data_sources.json into BaseHub.procs.
        The outer key is the file name with no extension.

        procs = { "data source": { "proc file name with no file ext": ... any number of keys/dict followed by:

        Special handling occurs when the file name is sql.json.  This procs in this file
        will be loaded into a general proc space that is accessible to all data sources.
        It can be accessed by using sql.myproc as the proc name passed to execute.

        --------------
        Statement dict
        --------------
        "proc name": { sql:"SQL statement",
                       host_type:"Optional key designating host type" }

           Parameters:
              dataSource - The name of the data source to load procs for

           Returns:
              None
        """

        if dataSource in BaseHub.dataSources and \
           'procs' in BaseHub.dataSources[dataSource] and \
           dataSource not in BaseHub.procs:

            BaseHub.procs[dataSource] = dict()

            for file in BaseHub.dataSources[dataSource]['procs']:

                ##Load file##
                procFileObj = open(file)
                try:
                    procFile = procFileObj.read()
                finally:
                    procFileObj.close()

                ##Use file name as key##
                head, tail = os.path.split(file)
                name, ext = os.path.splitext(tail)

                if name in BaseHub.procs[dataSource]:
                    ##Duplicate file name detected##
                    msg = 'A duplicate proc file, %s, was found in the data source %s.  Please change the file name.' % (file, dataSource)
                    raise DataHubError(msg)

                if 'sql.json' in file:
                    BaseHub.procs['sql'].update( { name:BaseHub.deserializeJson(procFile) } )
                else:
                    BaseHub.procs[dataSource].update( { name:BaseHub.deserializeJson(procFile) } )

    @staticmethod
    def getProc(dataSource, proc):
        """
        Returns the requested procedure from the BaseHub.procs data structure.

           Parameters:
              dataSource - The name of the data source to retrieve procs from
              proc - The full '.' delimieted path to the proc. ex: proc_file.selects.proc_name

           Returns:
              Data structure containing the requested procedure
        """
        procStruct = None
        fields = proc.split('.')

        ####
        # A base name of sql allows clients to
        # store general purpose sql that is
        # available for all data sources
        ####
        sql = False
        if fields[0] == 'sql':
            dataSource = 'sql'

        for i in range(len(fields)):
            key = fields[i]
            try:
                if i == 0:
                    procStruct = BaseHub.procs[dataSource][key]
                else:
                    procStruct = procStruct[key]
            except KeyError:
                msg = "The key, %s, provided in %s was not found in the data source %s in %s" % (key, proc, dataSource, BaseHub.sourceListFile)
                raise DataHubError(msg)

        return procStruct

    @staticmethod
    def addDataSource(dataSourceStruct):
        """
        Adds a datasource data structure to BaseHub.dataSources and loads the
        associated proc files.  Raises DataHubError if the dataSource already
        exists.

        Parameters:
           dataSourceStruct - A datasource structure.

        Returns:
           None
        """
        for dataSource in dataSourceStruct:

            if dataSource not in BaseHub.dataSources:
                ##Load the new source##
                BaseHub.dataSources[dataSource] = dataSourceStruct[dataSource]

                ##Load the procs##
                BaseHub.loadProcs(dataSource)

    @staticmethod
    def loadBuiltinProcs(arg, dirname, names):
        for fileName in names:
            name, fileExt = os.path.splitext(fileName)
            if fileExt == '.json':
                BaseHub.builtInProcs.append("%s/%s"%(dirname,fileName))
    """
    Member Functions
    """
    def getDataSourceConfig(self, dataSourceName):

        if dataSourceName in BaseHub.dataSources:
            return BaseHub.dataSources[dataSourceName]

        msg = 'The data source, %s, was not found.  Available datasources include %s.'
        raise DataHubError(msg%(dataSourceName, ','.join(BaseHub.dataSources.keys())))

"""
Error classes
"""
class DataHubError:
    """Base class for all data hub errors.  Takes an error message and returns string representation in __repr__."""
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return self.msg

class DataSourceKeyError(DataHubError):
    """Dictionary key error.  Raised when a required key or key value is not defined"""
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return self.msg

if not BaseHub.dataSources:
    """
    Initialize BaseHub class variable data only once.
    """
    if not BaseHub.dataSources:

        ####
        # load the data_sources.json file
        # its used for unit tests
        ####
        procsPath = os.path.dirname(__file__).replace('bases', BaseHub.defaultProcDir)
        os.path.walk(procsPath, BaseHub.loadBuiltinProcs, {})

        testDataSourcePath = os.environ.get(
           "DATASOURCES",
           os.path.join(
              os.path.dirname(os.path.dirname(__file__)),
              BaseHub.defaultDataSourceFile
              )
           )

        BaseHub.getSources(testDataSourcePath, True)

        #####
        #Load datasource file specified by env variable
        #####
        if BaseHub.dataSourceEnv in os.environ:
            BaseHub.sourceListFile = os.environ[BaseHub.dataSourceEnv]

            ##Get the data sources##
            BaseHub.getSources(BaseHub.sourceListFile, False)
