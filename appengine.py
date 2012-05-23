from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import os, sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

os.environ["DJANGO_SETTINGS_MODULE"] = "datazilla.datazilla.settings.base"

# Force relaod django setting
from django.conf import settings
settings._target = None

import logging
import django.core.handlers.wsgi
import django.core.signals
import django.db
import django.dispatch.dispatcher
from django.core.handlers.wsgi import WSGIHandler

def log_exception(*args, **kwds):
    logging.exception('Exception in request:')

if not os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    # Log errors.
    django.dispatch.dispatcher.connect(
        log_exception, django.core.signals.got_request_exception)

    # Unregister the rollback event handler.
    django.dispatch.dispatcher.disconnect(
        django.db._rollback_on_exception,
        django.core.signals.got_request_exception)

def main():
    application = WSGIHandler()
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
