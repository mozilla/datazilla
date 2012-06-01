"""
Provides a SQLDataSource class which reads datasource configuration from the
datasource table.

"""
import datetime
import os
import subprocess

from datasource.bases.BaseHub import BaseHub
from datasource.hubs.MySQL import MySQL
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
import MySQLdb


# the cache key is specific to the database name we're pulling the data from
SOURCES_CACHE_KEY = "{database}-datasources"

SQL_PATH = os.path.dirname(os.path.abspath(__file__))



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

        Raises ``DatasetNotFoundError`` if no dataset is found for the given
        project and contenttype. Otherwise, uses the latest dataset for that
        project and contenttype.

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

        if not candidate_sources:
            raise DatasetNotFoundError(
                "No active dataset found for project %r, contenttype %r."
                % (self.project, self.contenttype)
                )

        candidate_sources.sort(key=lambda s: s.dataset, reverse=True)

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


    @classmethod
    @transaction.commit_on_success
    def create(
        cls, project, contenttype=None, dataset=None, host=None, name=None):
        """
        Create a new ``SQLDataSource`` and its corresponding database.

        Required arguments:

        ``project``
            The name of the project to create a database for.

        Optional arguments:

        ``contenttype``
            The contenttype of this datasource; defaults to "perftest".

        ``dataset``
            The dataset number; defaults to 1 higher than the highest existing
            dataset for this project; or 1 if none exist.

        ``host``
            The host on which to create this database; defaults to
            ``DATAZILLA_DATABASE_HOST``.

        ``name``
            The name of the database to create; defaults to
            ``project_contenttype_dataset``.

        Assumes that the database server at ``host`` is accessible, and that
        ``DATAZILLA_DATABASE_USER`` (identified by
        ``DATAZILLA_DATABASE_PASSWORD`` exists on it and has permissions to
        create databases.

        """
        if contenttype is None:
            contenttype = "perftest"
        if dataset is None:
            try:
                dataset = DataSource.objects.filter(
                    project=project, contenttype=contenttype).order_by(
                    "-dataset")[0].dataset + 1
            except IndexError:
                dataset = 1
        if host is None:
            host = settings.DATAZILLA_DATABASE_HOST
        if name is None:
            name = "{0}_{1}_{2}".format(project, contenttype, dataset)

        ds = DataSource.objects.create(
            host=host,
            project=project,
            contenttype=contenttype,
            dataset=dataset,
            name=name,
            type="MySQL",
            creation_date=datetime.datetime.now(),
            )

        ds.create_database()

        sqlds = cls(project, contenttype)
        sqlds._dhub = ds.dhub(sqlds.procs_file_name)
        return sqlds



class DataSourceManager(models.Manager):
    def cached(self):
        """Return all datasources, caching the results."""
        from django.db import connections
        sources = cache.get(
            SOURCES_CACHE_KEY.format(
                database=connections["default"].settings_dict["NAME"])
            )
        if sources is None:
            sources = list(self.all())
            cache.set(SOURCES_CACHE_KEY, sources)
        return sources



class DataSource(models.Model):
    """
    A dataset for a source of data for a single project / contenttype.

    """
    project = models.CharField(max_length=25)
    dataset = models.IntegerField()
    contenttype = models.CharField(max_length=25)
    host = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    type = models.CharField(max_length=25)
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


    def create_database(self, sql_schema_file=None):
        """
        Create the database for this source, using given SQL schema file.

        Assumes that the database server at ``self.host`` is accessible, and
        that ``DATAZILLA_DATABASE_USER`` (identified by
        ``DATAZILLA_DATABASE_PASSWORD`` exists on it and has permissions to
        create databases.

        """
        if sql_schema_file is None:
            sql_schema_file = os.path.join(
                SQL_PATH, "template_schema", "schema_perftest.sql")

        conn = MySQLdb.connect(
            host=self.host,
            user=settings.DATAZILLA_DATABASE_USER,
            passwd=settings.DATAZILLA_DATABASE_PASSWORD,
            )
        cur = conn.cursor()
        cur.execute("CREATE DATABASE {0}".format(self.name))
        conn.close()

        # MySQLdb provides no way to execute an entire SQL file in bulk, so we
        # have to shell out to the commandline client.
        with open(sql_schema_file) as f:
            subprocess.check_call(
                [
                    "mysql",
                    "--host={0}".format(self.host),
                    "--user={0}".format(settings.DATAZILLA_DATABASE_USER),
                    "--password={0}".format(
                        settings.DATAZILLA_DATABASE_PASSWORD),
                    self.name,
                    ],
                stdin=f,
                )
