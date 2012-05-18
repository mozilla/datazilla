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
import sys
import pprint
import imp
import optparse
import subprocess

try:
    import simplejson as json
except ImportError:
    import json

from datasource.bases.BaseHub import BaseHub, DataHubError, DataSourceKeyError

class DataHub:

    ##Location of all base hub derived classes##
    dataHubDir = os.path.dirname(__file__) + '/hubs/'
    """
    dict( "Module name": dict( source="full file path to module source",
                               compiled="full path to compiled module if it exists" )
    """
    dataHubClasses = dict()

    @staticmethod
    def get(dataSourceName):
        """
        Staticmethod that imports the requested data hub module and returns a class instance.

        Parameters:
           dataSourceName - String containing unique data source name found in data_source.json file.

        Returns:
           Instance of the appropriate data hub class
        """
        ##Find the module name##
        moduleName = None
        if dataSourceName in BaseHub.dataSources:
            if 'hub' in BaseHub.dataSources[dataSourceName]:
                moduleName = BaseHub.dataSources[dataSourceName]['hub']
            else:
                raise DataSourceKeyError()

        if not moduleName:
            raise DataSourceNotFoundError(dataSourceName)

        ##Load the module##
        module = None
        if moduleName in DataHub.dataHubClasses:
            mod = DataHub.dataHubClasses[moduleName]
            if mod['compiled']:
                ##Use the compiled module if we have it##
                module = imp.load_compiled(moduleName, mod['compiled'])
            elif mod['source']:
                module = imp.load_source(moduleName, mod['source'])

        if not module:
            ##Whoa there skippy! Something horrible has happened##
            raise DataHubNotFoundError(moduleName)

        ##Get the class##
        class_ = getattr(module, moduleName)

        ##Yer all clear kid! instantiate the data hub class##
        return class_(dataSourceName)

    @staticmethod
    def getDataSourceModuleCallback(arg, dirname, names):
        """
        Callback for os.path.walk.  Loads the module name and full path to
        the source and compiled version if it exists.  I was thinking this
        would be a nice feature for a developer (likely me) writing a data hub class
        so they don't have to remember to import the class in DataHub manually
        but it feels a bit hacky...

        One bit of suck associated with this is when the .pyc file is imported
        directly python does not figure out that there is a difference between
        it and the source, so when developing a data hub and testing through
        DataHub the developer has to sometimes remove the .pyc file manually.
        Probably going to get rid of this in the future if I cannot find a better
        way to do it.

        Parameters:
           arg - additional arguments
           dirname - directory name
           names - list of directory contents

        Returns:
           None
        """
        for fileName in names:

            moduleName, fileExt = os.path.splitext(fileName)

            if moduleName == '__init__' or moduleName[0] == '.':
                #Skip __init__ files and file names beginning with a '.'
                continue
            if moduleName not in DataHub.dataHubClasses:
                DataHub.dataHubClasses[moduleName] = dict( source="", compiled="" )
            if fileExt == '.pyc':
                DataHub.dataHubClasses[moduleName]['compiled'] = dirname + fileName
            if fileExt == '.py':
                DataHub.dataHubClasses[moduleName]['source'] = dirname + fileName

    @staticmethod
    def showDataHubModules():
        """
        Prints a list of all available data hub classes stdout.

           Parameters:
              None

           Returns:
              None
        """
        pp = pprint.PrettyPrinter(indent=3)
        pp.pprint(DataHub.dataHubClasses)

class DataHubNotFoundError(DataHubError):
    def __init__(self, moduleName):
        self.moduleName = moduleName
    def __repr__(self):
        classKeys = DataHub.dataHubClasses.keys()
        return "The DataHub class requested, %s, was not found.  The available data hub modules include: %s" % (self.moduleName, ','.join(classKeys))

class DataSourceNotFoundError(DataHubError):
    def __init__(self, dataSourceName):
        self.dataSourceName = dataSourceName
    def __repr__(self):
        dataSourceKeys = DataHub.dataSources.keys()
        return "The data source requested, %s, was not found.  The available data sources include: %s" % (self.dataSourceName, ','.join(dataSourceKeys))

if not DataHub.dataHubClasses:
    """
    Load the names and paths of all of the derived data source
    modules available.  The class variable dataHubClasses will
    only be loaded a single time when the DataHub is
    imported.
    """
    os.path.walk(DataHub.dataHubDir,
                 DataHub.getDataSourceModuleCallback,
                 DataHub.dataHubClasses)

def main(options, args, parser):

    if not len(args) == 1:
        print "No datasource provided"
        parser.print_help()
        sys.exit(0)

    kwargs = dict()

    ####
    #There must be a better way of doing this! The options
    #in the options object returned by parser.parse_args()
    #are not directly iterable... This much
    #hardcoding makes me sad :-(
    ####
    schar = ","
    if options.db:
        kwargs['db'] = options.db
    if options.proc:
        kwargs['proc'] = options.proc
    if options.host_type:
        kwargs['host_type'] = options.host_type
    if options.placeholders:
        kwargs['placeholders'] = options.placeholders.split(schar)
    if options.replace:
        kwargs['replace'] = options.replace.split(schar)
    if options.replace_quote:
        kwargs['replace_quote'] = options.replace_quote.split(schar)
    if options.limit:
        kwargs['limit'] = options.limit
    if options.offset:
        kwargs['offset'] = options.offset
    if options.key_column:
        kwargs['key_column'] = options.key_column
    if options.return_type:
        kwargs['return_type'] = options.return_type
    if options.debug_show:
        kwargs['debug_show'] = options.debug_show
    if options.debug_noex:
        kwargs['debug_noex'] = options.debug_noex

    dh = DataHub.get(args[0])
    d = dh.execute(**kwargs)

    if type(d) == type(''):
        #####
        #User requested json, write it to stdout but make it
        #pretty first with the -mjson.tool flag to python.
        #It's a bit hackish but could not figure out how to
        #do this directly in this module
        #####
        proc = subprocess.Popen(['python',  '-mjson.tool'],
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE)

        stdoutValue = proc.communicate(input="%s"%d)
        print stdoutValue[0]
    else:
        ###
        #All other return types available to the command line tool
        #can be printed with pretty printer
        pp = pprint.PrettyPrinter(indent=3)
        pp.pprint(d)

def loadOptionGroup(parser, options, action):

    for o in options:

        option = o[0]
        soption = o[1]
        help = o[2]
        doption = '--%s'%option

        if action:
            parser.add_option(soption, doption, action='store_true', dest=option, help=help)
        else:
            parser.add_option(soption, doption, dest=option, help=help)

if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.set_defaults(verbose=True)

    parser.set_usage("%s [OPTIONS]...[datasource]\n\nProvides a "%os.path.split(sys.argv[0])[1]+\
                     "command line interface to the datasource hub's\nexecute function. "+\
                     "For more extensive docs see the README in datasource.")

    executeOptions = (('db', '-d', 'Name of database to connect to. Optional, if set in datasource.'),
                      ('proc', '-p', 'Name of the procedure to call.'),
                      ('host_type', '-H', 'Possible values include master_host, read_host, or dev_host.  Defaults to master_host.'))


    procGroup = (('placeholders', '-P', 'A list of placeholder parameters for the proc.'),
                ('replace', '-r', 'A list of replacements to make in the proc.'+\
                   'REP0, REP1, REP2, REP3 etc... in the sql.'),
                ('replace_quote', '-q', 'Same as replace but the items from the list are quoted'),
                ('limit', '-l', 'A limit to append to the sql as LIMIT integer.'),
                ('offset', '-o', 'An offset to append to the sql as OFFSET integer.'),
                ('key_column', '-k', 'table.column to use as a key_column for return_types of dict* or set*'),
                ('return_type', '-R', 'Possible values are dict, dict_json, tuple, tuple_json, set, table, table_json, and set_json.  Defaults to list'))

    debugGroup = (('debug_show', '-s', 'Show SQL and other info about the query including execution time.'),
                  ('debug_noex', '-n', 'Show SQL and other info about the query without executing it.'))

    loadOptionGroup(parser, executeOptions, None)

    ##Group proc related options##
    pgroup = optparse.OptionGroup(parser, "Proc Options")
    loadOptionGroup(pgroup, procGroup, None)
    ##Group Debug Options##
    dgroup = optparse.OptionGroup(parser, "Debug Options")
    loadOptionGroup(dgroup, debugGroup, True)

    parser.add_option_group(pgroup)
    parser.add_option_group(dgroup)

    (options, args) = parser.parse_args()

    main(options, args, parser)
