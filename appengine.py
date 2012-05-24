import os, sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

os.environ["DJANGO_SETTINGS_MODULE"] = "datazilla.settings.base"

from google.appengine.ext.webapp.util import run_wsgi_app
from django.core.handlers.wsgi import WSGIHandler

def main():
    application = WSGIHandler()
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
