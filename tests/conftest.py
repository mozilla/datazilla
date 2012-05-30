import os

from datazilla.vendor import add_vendor_lib


def pytest_sessionstart(session):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")
    add_vendor_lib()
