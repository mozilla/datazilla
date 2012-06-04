import os

from django.conf import settings
from datasource.bases.BaseHub import BaseHub
from datasource.hubs.CloudSQL import CloudSQL
from datazilla.models import SQLDataSource, SQL_PATH



class CloudSQLDataSource(SQLDataSource):
    def _get_dhub(self):
        data_source = {
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
        BaseHub.add_data_source(data_source)

        try:
            return CloudSQL(self.project)
        except KeyError:
            raise KeyError("Failed to create CloudSQL")
