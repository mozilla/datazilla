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
        self._datasource = None
        self._dhub = None


    def __unicode__(self):
        """Unicode representation is project and contenttype."""
        return "{0} - {1}".format(self.project, self.contenttype)


    @property
    def datasource(self):
        """The DataSource model object backing this SQLDataSource."""
        if self._datasource is None:
            self._datasource = self._get_datasource()
        return self._datasource


    @property
    def dhub(self):
        """
        The configured datahub for this data source.

        Raises ``DatasetNotFoundError`` if no dataset is found for the given
        project and contenttype. Otherwise, uses the latest dataset for that
        project and contenttype.

        """
        if self._dhub is None:
            self._dhub = self.datasource.dhub(self.procs_file_name)
        return self._dhub


    def _get_datasource(self):
        candidate_sources = []
        for source in DataSource.objects.cached():
            if (source.project == self.project and
                    source.contenttype == self.contenttype):
                candidate_sources.append(source)

        if not candidate_sources:
            raise DatasetNotFoundError(
                "No dataset found for project %r, contenttype %r."
                % (self.project, self.contenttype)
                )

        candidate_sources.sort(key=lambda s: s.dataset, reverse=True)

        return candidate_sources[0]

    def disconnect(self):
        self.dhub.disconnect()


    def create_next_dataset(self, schema_file=None):
        """
        Create and return the next dataset for this project/contenttype.

        The database for the new dataset will be located on the same host.

        """
        dataset = DataSource.objects.filter(
            project=self.project,
            contenttype=self.contenttype
            ).order_by("-dataset")[0].dataset + 1

        # @@@ should we store the schema file name used for the previous
        # dataset in the db and use the same one again automatically? or should
        # we actually copy the schema of an existing dataset rather than using
        # a schema file at all?
        return self._create_dataset(
            project=self.project,
            contenttype=self.contenttype,
            dataset=dataset,
            host=self.datasource.host,
            db_type=self.datasource.type,
            schema_file=schema_file,
            )


    @classmethod
    def create(cls, project, contenttype,
               host=None, name=None, db_type=None, schema_file=None):
        """
        Create and return a new datasource for given project/contenttype.

        Creates the database ``name`` (defaults to "project_contenttype_1") on
        host ``host`` (defaults to ``DATAZILLA_DATABASE_HOST``) and populates
        the template schema from ``schema_file`` (defaults to
        ``template_schema/schema_<contenttype>.sql``) using the db type
        ``db_type`` (defaults to "MySQL-InnoDB").

        Assumes that the database server at ``host`` is accessible, and that
        ``DATAZILLA_DATABASE_USER`` (identified by
        ``DATAZILLA_DATABASE_PASSWORD`` exists on it and has permissions to
        create databases.

        """
        if host is None:
            host = settings.DATAZILLA_DATABASE_HOST

        return cls._create_dataset(
            project=project,
            contenttype=contenttype,
            dataset=1,
            host=host,
            name=name,
            db_type=db_type,
            schema_file=schema_file,
            )


    @classmethod
    @transaction.commit_on_success
    def _create_dataset(cls, project, contenttype, dataset, host,
                        name=None, db_type=None, schema_file=None):
        """Create a new ``SQLDataSource`` and its corresponding database."""
        if name is None:
            name = "{0}_{1}_{2}".format(project, contenttype, dataset)
        if db_type is None:
            db_type = "MySQL-InnoDB"

        ds = DataSource.objects.create(
            host=host,
            project=project,
            contenttype=contenttype,
            dataset=dataset,
            name=name,
            type=db_type,
            creation_date=datetime.datetime.now(),
            )

        ds.create_database(schema_file)

        sqlds = cls(project, contenttype)
        sqlds._datasource = ds
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
        unique_together = [
            ["project", "dataset", "contenttype"],
            ["host", "name"],
            ]


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
                # @@@ this should depend on self.type
                # @@@ shouldn't have to specify this here and below
                "hub": "MySQL",
                "master_host": {
                    "host": self.host,
                    "user": settings.DATAZILLA_DATABASE_USER,
                    "passwd": settings.DATAZILLA_DATABASE_PASSWORD,
                    },
                "default_db": self.name,
                "procs": [
                    os.path.join(SQL_PATH, procs_file_name),
                    #os.path.join(SQL_PATH, "sql.json"),
                    ],
                }
            }
        BaseHub.add_data_source(data_source)
        # @@@ the datahub class should depend on self.type
        return MySQL(self.key)


    def create_database(self, schema_file=None):
        """
        Create the database for this source, using given SQL schema file.

        If schema file is not given, defaults to
        "template_schema/schema_<contenttype>.sql.tmpl".

        Assumes that the database server at ``self.host`` is accessible, and
        that ``DATAZILLA_DATABASE_USER`` (identified by
        ``DATAZILLA_DATABASE_PASSWORD`` exists on it and has permissions to
        create databases.

        """
        if self.type.lower().startswith("mysql-"):
            engine = self.type[len("mysql-"):]
        elif self.type.lower() == "mysql":
            engine = "InnoDB"
        else:
            raise NotImplementedError(
                "Currently SQLDataSource supports only MySQL data sources.")

        if schema_file is None:
            schema_file = os.path.join(
                SQL_PATH,
                "template_schema",
                "schema_{0}.sql.tmpl".format(self.contenttype),
                )

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
        with open(schema_file) as f:
            # set the engine to use
            sql = f.read().format(engine=engine)

        args = [
            "mysql",
            "--host={0}".format(self.host),
            "--user={0}".format(settings.DATAZILLA_DATABASE_USER),
            ]
        if settings.DATAZILLA_DATABASE_PASSWORD:
            args.append(
                "--password={0}".format(
                    settings.DATAZILLA_DATABASE_PASSWORD)
                )
        args.append(self.name)
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            )
        (output, _) = proc.communicate(sql)
        if proc.returncode:
            raise IOError(
                "Unable to set up schema for datasource {0}: "
                "mysql returned code {1}, output follows:\n\n{2}".format(
                    self.key, proc.returncode, output)
                )
