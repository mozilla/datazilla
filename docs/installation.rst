Installation
================

* Install memcached, MySQL, a WSGI application server, and a static
  files web server (in some cases, e.g. Apache, the latter two could be
  the same server).

* Install the compiled dependencies in ``requirements/compiled.txt`` via
  system package manager or via::

    pip install -r requirements/compiled.txt

* Configure the WSGI application server to serve the application object
  in ``datazilla/wsgi.py`` at the root of the domain, and configure the
  static files server to serve the files in ``datazilla/webapp/static``
  at the URL path ``/static/``. See the sample config files for Apache
  and nginx in ``datazilla/webapp/sample_configs/``.

* Copy ``datazilla/settings/local.sample.py`` to
  ``datazilla/settings/local.py`` and edit the settings it contains to the
  correct values for your installation. ``DATAZILLA_MEMCACHED`` should be a
  string like ``127.0.0.1:11211`` - the host and port at which memcached is
  running.

* Run ``python manage.py syncdb`` to create the core datasource table.

* Create a paired objectstore and performance test database with the manage.py create_perftest_project command::

    manage.py create_perftest_project [options]

    Create all databases for a new project.

    Options:
        -p PROJECT, --project=PROJECT
                        Set the project to run on: talos, b2g, schema, test
                        etc....
        --perftest_host=PERFTEST_HOST
                        The host name for the perftest database
        --objectstore_host=OBJECTSTORE_HOST
                        The host name for the objectstore database
        --perftest_type=PERFTEST_TYPE
                        The database type (e.g. 'MySQL-InnoDB') for the
                        perftest database
        --objectstore_type=OBJECTSTORE_TYPE
                        The database type (e.g. 'MySQL-Aria') for the
                        objectstore database
        --cron_batch=CRON_BATCH
                        Add this new project to this cron_batch. This value
                        indicates the size of the project and may determine
                        how much time between intervals should be set.  Larger
                        projects will likely have a longer time interval
                        between execution as cron jobs.Choices are: small,
                        medium, large.  Default to None.

* Install crontab.txt
