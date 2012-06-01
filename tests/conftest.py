import os
from random import choice
from string import letters

from datazilla.vendor import add_vendor_lib


def pytest_sessionstart(session):
    """
    Set up the test environment.

    Sets DJANGO_SETTINGS_MODULE, adds the vendor lib, and sets up a test
    database.

    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")
    add_vendor_lib()

    from django.test.simple import DjangoTestSuiteRunner
    # we don't actually let Django run the tests, but we need to use some
    # methods of its runner for setup/teardown of dbs and some other things
    session.django_runner = DjangoTestSuiteRunner()
    # this provides templates-rendered debugging info and locmem mail storage
    session.django_runner.setup_test_environment()
    # this sets up a clean test-only database
    session.django_db_config = session.django_runner.setup_databases()

    # this effectively clears memcached to make tests deterministic
    from django.core.cache import cache
    cache.key_prefix = "t-" + "".join([choice(letters) for i in range(5)])


def pytest_sessionfinish(session):
    """Tear down the test environment, including databases."""
    print("\n")
    session.django_runner.teardown_databases(session.django_db_config)
    session.django_runner.teardown_test_environment()
