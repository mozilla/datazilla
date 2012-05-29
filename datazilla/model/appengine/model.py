import os

from django.conf import settings
from datasource.bases.BaseHub import BaseHub
from datasource.hubs.CloudSQL import CloudSQL
from datazilla.models import SQLDataSource, SQL_PATH



class CloudSQLDataSource(SQLDataSource):
    def _get_dhub(self):
        dataSource = {
            self.project : {
                "hub":"MySQL",
                "master_host":{
                    "host": settings.CLOUDSQL_INSTANCE,
                    # FIXME: CloudSQL has no users, but datasource requires it
                    "user": "none",
                    },
                "default_db": settings.CLOUDSQL_DATABASE,
                "procs": [os.path.join(SQL_PATH, self.procs_file_name)]
                }
            }
        BaseHub.addDataSource(dataSource)

        try:
            return CloudSQL(self.project)
        except KeyError:
            raise KeyError("Failed to create CloudSQL")
