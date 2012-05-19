import os, sys

# add root directory to sys.path as we can't count on mod_wsgi doing it
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

from datazilla.vendor import add_vendor_lib
add_vendor_lib()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
