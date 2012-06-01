"""
Provides a SQLDataSource class which reads datasource configuration from the
datasource table.

"""
import os

from datasource.bases.BaseHub import BaseHub
from datasource.hubs.MySQL import MySQL
from django.conf import settings
from django.core.cache import cache
from django.db import models


# the cache key is specific to the database name we're pulling the data from
SOURCES_CACHE_KEY = "{database}-datasources"

SQL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql")



class MultipleDatasetsError(ValueError):
    pass



class DatasetNotFoundError(ValueError):
    pass



class SQLDataSource(object):
    """
    Encapsulates SQL queries against a specific data source.

    """
    def __init__(self, project, contenttype, procs_file_name=None):
        """
        Initialize for given project, contenttype, procs file.

        If not supplied, procs file name defaults to the name of the
        contenttype with ``.json`` appended.

        """
        self.DEBUG = settings.DEBUG
        self.project = project
        self.contenttype = contenttype
        self.procs_file_name = procs_file_name or "%s.json" % contenttype
        self._dhub = None


    @property
    def dhub(self):
        """
        The configured datahub for this data source.

        Raises ``MultipleDatasetsError`` if multiple active datasets are found
        for the given project and contenttype.

        Raises ``DatasetNotFoundError`` if no active dataset is found for the
        given project and contenttype.

        """
        if self._dhub is None:
            self._dhub = self._get_dhub()
        return self._dhub


    def _get_dhub(self):
        candidate_sources = []
        for source in DataSource.objects.cached():
            if (source.project == self.project and
                    source.contenttype == self.contenttype):
                candidate_sources.append(source)

        # @@@ should we just pick the latest instead? would require switching
        # dataset to an integer field
        if len(candidate_sources) > 1:
            raise MultipleDatasetsError(
                "Project %r, contenttype %r has multiple active datasets: "
                % (
                    self.project,
                    self.contenttype,
                    ", ".join([s.dataset for s in candidate_sources])
                    )
                )
        elif not candidate_sources:
            raise DatasetNotFoundError(
                "No active dataset found for project %r, contenttype %r."
                % (self.project, self.contenttype)
                )

        return candidate_sources[0].dhub(self.procs_file_name)


    def set_data(self, statement, placeholders):

        self.dhub.execute(
            proc='perftest.inserts.' + statement,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            )


    def set_data_and_get_id(self, statement, placeholders):

        self.set_data(statement, placeholders)

        id_iter = self.dhub.execute(
            proc='perftest.selects.get_last_insert_id',
            debug_show=self.DEBUG,
            return_type='iter',
            )

        return id_iter.getColumnData('id')

    def disconnect(self):
        self.dhub.disconnect()



class DataSourceManager(models.Manager):
    def cached(self):
        """Return all datasources, caching the results."""
        from django.db import connections
        sources = cache.get(
            SOURCES_CACHE_KEY.format(
                database=connections["default"].settings_dict["NAME"])
            )
        if sources is None:
            sources = list(self.filter(active_status=True))
            cache.set(SOURCES_CACHE_KEY, sources)
        return sources



class DataSource(models.Model):
    """
    A source of data for a single project.

    """
    project = models.CharField(max_length=25)
    dataset = models.CharField(max_length=25)
    contenttype = models.CharField(max_length=25)
    host = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=25)
    active_status = models.BooleanField(default=True, db_index=True)
    creation_date = models.DateTimeField()

    objects = DataSourceManager()


    class Meta:
        db_table = "datasource"
        unique_together = [["project", "dataset", "contenttype"]]


    @property
    def key(self):
        """Unique key for a data source is the project, contenttype, dataset."""
        return "{0} - {1} - {2}".format(
            self.project, self.contenttype, self.dataset)


    def __unicode__(self):
        """Unicode representation is the project's unique key."""
        return unicode(self.key)


    def dhub(self, procs_file_name):
        """
        Return a configured ``DataHub`` using the given SQL procs file.

        """
        data_source = {
            self.key: {
                "hub": "MySQL",
                "master_host": {
                    "host": self.host,
                    "user": settings.DATAZILLA_DATABASE_USER,
                    "passwd": settings.DATAZILLA_DATABASE_PASSWORD,
                    },
                "default_db": self.name,
                "procs": [os.path.join(SQL_PATH, procs_file_name)],
                }
            }
        BaseHub.addDataSource(data_source)
        # @@@ the datahub class should depend on self.type
        return MySQL(self.key)
