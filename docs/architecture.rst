
.. _Architecture:

Architecture
==============

Top Level
-----------
There are four database schemas available in datazilla: :ref:`datazilla`, :ref:`schema_hgmozilla.sql.tmpl`, :ref:`schema_objectstore.sql.tmpl`, and :ref:`schema_perftest.sql.tmpl`. Three of these are template schemas that are used by manage commands to create new databases with the storage engine specified by the user.  Access to each schema is provided through the :ref:`model` layer.  The model layer is used by controllers to retrieve data in each of the schemas and is exposed to the user through a set of web service methods.

.. _datazilla:

datazilla
---------
This schema is accessed using the django ORM, the model for it is defined `here <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/models.py#L253>`_. and consists of a single table with the following structure.

+-----------------------+--------------+------+-----+---------+----------------+
| Field                 | Type         | Null | Key | Default | Extra          |
+=======================+==============+======+=====+=========+================+
| id                    | int(11)      | NO   | PRI | NULL    | auto_increment |
+-----------------------+--------------+------+-----+---------+----------------+
| project               | varchar(25)  | NO   | MUL | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| contenttype           | varchar(25)  | NO   |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| dataset               | int(11)      | NO   |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| host                  | varchar(128) | NO   |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| read_only_host        | varchar(128) | YES  |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| name                  | varchar(128) | NO   |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| type                  | varchar(25)  | NO   |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| oauth_consumer_key    | varchar(45)  | YES  |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| oauth_consumer_secret | varchar(45)  | YES  |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| creation_date         | datetime     | NO   |     | NULL    |                |
+-----------------------+--------------+------+-----+---------+----------------+
| cron_batch            | varchar(45)  | YES  |     | small   |                |
+-----------------------+--------------+------+-----+---------+----------------+

All databases storing data used by datazilla are stored as a row in this table.  Each database has three classifiers associated with it: project, contenttype, and dataset.  The name of the database is typically these three classifiers joined on an underscore but there is no requirement for this, the name can be any string.  There is no physical requirement for the databases referenced in this table to be co-located.  The only requirement is that both the web service and machine that run's the cron jobs have access to each of the databases in this table.  Any database can have OAuth credentials associated with it but they are not required so the field can be null.  Currently the only databases that require OAuth are the objectstore and only for the storage of the JSON object.  Each database can also have a cron batch interval associated with it.  This interval specifies the time interval of cron jobs run.

**project** - A descriptive string associated with the project: talos, b2g, schema etc... This string becomes the location field in the url for related web service methods.

**contenttype** - A string describing the content type associated with the database.  The perftest content type stores performance test results, the objectstore content type stores JSON objects in it.  A project can have any number of contenttypes associated with it.

**dataset** - An integer that can be enumerated.  This allows more than one database to exist for the same project/contenttype pair.

**host** - Name of the database host.

**read_only_host** - A read only host associated with the database.

**name** - Name of the database.

**type** - Type of storage engine associated with the database.  This is automatically added to the template schema when a user runs a manage command that creates a database schema.  There is currently support for MariaDB and MySQL storage engines.

**oauth_consumer_key** - The OAuth consumer key.  This is created for databases with objectstores automatically by the create_project manage command.

**oauth_consumer_secret** - The OAuth consumer secret.  This is created for databases with objectstores automatically by the create_project manage command.

**creation_date** - Date the database was created.

**cron_batch** - The cron interval to use when running cron jobs on this database.

.. _schema_hgmozilla.sql.tmpl:

schema_hgmozilla.sql.tmpl
-------------------------
The `hgmozilla schema <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/template_schema/schema_hgmozilla.sql.tmpl>`_ currently holds the mozilla mercurial push log data.  However, the only part of it that's specific to mercurial is the web service method used to retrieve data to populate it.  The data used to populate the schema is generated by the `json-pushes <https://hg.mozilla.org/mozilla-central/json-pushes?full=1&maxhours=24>`_ web service method.  The manage command, update_pushlog, calls this web service method and populates the associated schema.  The data can be used to create an ordered list of code base changes pushed to the build/test system.  This is required for any statistical method that requires a comparison between a push and its parent.

.. _schema_objectstore.sql.tmpl:

schema_objectstore.sql.tmpl
---------------------------
The `objectstore schema <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/template_schema/schema_objectstore.sql.tmpl>`_ holds the unprocessed json objects submitted to the project.  When objects are successfully processed into a corresponding index the `test_run_id` field is populated with an integer.  The `test_run_id` corresponds to the `test_run.id` field in the `perftest schema <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/template_schema/schema_perftest.sql.tmpl#L549>`_.

.. _schema_perftest.sql.tmpl:

schema_perftest.sql.tmpl
------------------------
This `perftest schema <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/template_schema/schema_perftest.sql.tmpl>`_ translates the JSON structure in the objectstore into a relational index.  It also contains tables for the storage of statistical data generated post object submission.

.. _model:

Model
----------
The model layer found in `/datazilla/model <https://github.com/mozilla/datazilla/tree/master/datazilla/model>`_ provides an interface for getting/setting data in a database. The datazilla model classes rely on a module called `datasource <https://github.com/jeads/datasource>`_. This module encapsulates SQL manipulation. All of the SQL used by the system is stored in JSON files found in `/datazilla/model/sql <https://github.com/mozilla/datazilla/tree/master/datazilla/model/sql>`_. There can be any number of SQL files stored in this format. The JSON structure allows SQL to be stored in named associative arrays that also contain the host type to be associated with each statement. Any command line script or web service method that requires data should use a derived model class to obtain it. ::


    ptm = PerformanceTestModel(project)
    products = ptm.get_product_test_os_map()

The ``ptm.get_product_test_os_map()`` method looks like this::

        def get_product_test_os_map(self):
            proc = 'perftest.selects.get_product_test_os_map'

            product_tuple = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                return_type='tuple',
                )

            return product_tuple

``perftest.selects.get_product_test_os_map`` found in `datazilla/model/sql/perftest.json <https://github.com/mozilla/datazilla/blob/master/datazilla/model/sql/perftest.json>`_ looks like this::

    {
        "selects":{

           "get_product_test_os_map":{

              "sql":"SELECT b.product_id, tr.test_id, b.operating_system_id
                     FROM test_run AS tr
                     LEFT JOIN build AS b ON tr.build_id = b.id
                     WHERE b.product_id IN (
                       SELECT product_id
                       FROM product )
                    GROUP BY b.product_id, tr.test_id, b.operating_system_id",

               "host":"master_host"
           },

           "...more SQL statements..."
    }

The string, ``perftest``, in ``perftest.selects.get_product_test_os_map`` refers to the SQL file name to load in `/datazilla/model/sql <https://github.com/mozilla/datazilla/tree/master/datazilla/model/sql>`_.  The SQL in perftest.json can also be written with placeholders and a string replacement system, see `datasource <https://git    hub.com/jeads/datasource>`_ for all of the features available.

