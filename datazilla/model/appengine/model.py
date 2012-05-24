
import os

from django.conf import settings

from datasource.bases.BaseHub import BaseHub
from datasource.hubs.CloudSQL import CloudSQL

class Model:
    def __init__(self, project, sqlFileName):
        self.DEBUG = settings.DEBUG

        Model.rootPath = os.path.dirname(os.path.abspath(__file__))

        dataSource = { project :
            { "hub":"MySQL",
              "master_host":{
                "host": settings.CLOUDSQL_INSTANCE,
                "user": settings.CLOUDSQL_USERNAME, # FIXME: Cloud SQL doesn't have an user. Delete it.
              },
              "default_db": settings.CLOUDSQL_DATABASE,
              "procs": ["%s/%s" % (Model.rootPath, '../sql/graphs.json')]
            } }
        BaseHub.addDataSource(dataSource)

        try:
            self.dhub = CloudSQL(project)
        except KeyError:
#            allProjects =  ','.join( Model.projectHub.keys() )
#            m = '%s project name is not recognized, available projects include: %s' % (self.project, allProjects)
            raise KeyError("Failed to create CloudSQL")

    # FIXME: Following methods are copied and pasted from model.sql.model.
    # We should share more code. Maybe create a common super class?

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
