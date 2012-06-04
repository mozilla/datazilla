Installation
================
* Install memcached, MySQL, a WSGI application server, and a static files web server (in some cases, e.g. Apache, the latter two could be the same server).
* Install the compiled dependencies in ``requirements/compiled.txt`` via system package manager or via ::

    pip install -r requirements/compiled.txt.

* Configure the WSGI application server to serve the application object in datazilla/wsgi.py at the root of the domain, and configure the static files server to serve the files in datazilla/webapp/static at the URL path ``/static/``. See the sample config files for Apache and nginx in ``datazilla/webapp/sample_configs``.
* Copy ``datazilla/settings/local.sample.py`` to ``datazilla/settings/local.py`` and edit the settings it contains to the correct values for your installation.

