#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
import sys
import os
import re

from datasource.bases.BaseHub import BaseHub
from datasource.hubs.MySQL import MySQL

class Model:

    projectHub = {}
    databaseSources = {}

    @staticmethod
    def loadvars():

        #####
        #Only load the database sources once when the module
        #is imported
        #####
        if not Model.projectHub:

            Model.DATAZILLA_DATABASE_NAME     = \
                os.environ["DATAZILLA_DATABASE_NAME"]
            Model.DATAZILLA_DATABASE_USER     = \
                os.environ["DATAZILLA_DATABASE_USER"]
            Model.DATAZILLA_DATABASE_PASSWORD = \
                os.environ["DATAZILLA_DATABASE_PASSWORD"]
            Model.DATAZILLA_DATABASE_HOST     = \
                os.environ["DATAZILLA_DATABASE_HOST"]
            Model.DATAZILLA_DATABASE_PORT     = \
                os.environ["DATAZILLA_DATABASE_PORT"]

            ####
            #Configuration of datasource hub:
            # 1 Build the datasource struct
            # 2 Add it to the BaseHub
            # 3 Instantiate a MySQL hub for all derived classes
            ####
            Model.rootPath = os.path.dirname(os.path.abspath(__file__))

            dataSource = { Model.DATAZILLA_DATABASE_NAME :

                            { "hub":"MySQL",
                              "master_host":

                                { "host":Model.DATAZILLA_DATABASE_HOST,
                                  "user":Model.DATAZILLA_DATABASE_USER,
                                  "passwd":Model.DATAZILLA_DATABASE_PASSWORD
                                },

                              "default_db":Model.DATAZILLA_DATABASE_NAME,
                              "procs": ["%s/%s" % (Model.rootPath,
                                                   'sources.json')]
                         } }

            BaseHub.addDataSource(dataSource)
            dzHub = MySQL(Model.DATAZILLA_DATABASE_NAME)

            Model.databaseSources = dzHub.execute(proc='sources.get_datasources',
                                                  key_column='project',
                                                  return_type='dict')

            Model.loadProjectHub(Model.databaseSources)

    @staticmethod
    def loadProjectHub(databaseSources):

        for s in databaseSources:

            project = databaseSources[s]['project']

            dataSource = { project :
                { "hub":"MySQL",
                  "master_host":{"host":databaseSources[s]['host'],
                  "user":Model.DATAZILLA_DATABASE_USER,
                  "passwd":Model.DATAZILLA_DATABASE_PASSWORD},
                  "default_db":databaseSources[s]['name'],
                  "procs": ["%s/%s" % (Model.rootPath, 'graphs.json')]
                } }

            BaseHub.addDataSource(dataSource)
            hub = MySQL( project )
            Model.projectHub[ project ] = hub

    def __init__(self, project, sqlFileName):

        self.project = project
        self.sqlFileName = sqlFileName

        try:
            self.DEBUG = os.environ["DATAZILLA_DEBUG"] is not None
        except KeyError:
            self.DEBUG = False

        #####
        #Set the hub to the requested project
        #####
        try:
            self.dhub = Model.projectHub[self.project]
        except KeyError:
            allProjects =  ','.join( Model.projectHub.keys() )
            m = '%s project name is not recognized, available projects include: %s' % (self.project, allProjects)
            raise KeyError(m)

    def setData(self, statement, placeholders):

        self.dhub.execute(proc='graphs.inserts.' + statement,
                          debug_show=self.DEBUG,
                          placeholders=placeholders)

    def setDataAndGetId(self, statement, placeholders):

        self.setData(statement, placeholders)

        idIter = self.dhub.execute(proc='graphs.selects.get_last_insert_id',
                                    debug_show=self.DEBUG,
                                    return_type='iter')

        return idIter.getColumnData('id')

    def isNumber(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def buildReplacement(self, colData):

        rep = "AND "

        for key in colData:
            if len(colData[key]) > 0:
                rep += key + ' IN (' + colData[key] + ') AND '

        rep = re.sub('AND\s+$', '', rep)

        return rep

    def disconnect(self):
        self.dhub.disconnect()


Model.loadvars()
