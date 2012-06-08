from functools import partial
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

    from datazilla.model import DatazillaModel
    DatazillaModel.create("testproj")


def pytest_sessionfinish(session):
    """Tear down the test environment, including databases."""
    print("\n")

    from django.conf import settings
    from datazilla.model import DatazillaModel
    import MySQLdb

    for sds in DatazillaModel("testproj").sources.values():
        conn = MySQLdb.connect(
            host=sds.datasource.host,
            user=settings.DATAZILLA_DATABASE_USER,
            passwd=settings.DATAZILLA_DATABASE_PASSWORD,
            )
        cur = conn.cursor()
        cur.execute("DROP DATABASE {0}".format(sds.datasource.name))
        conn.close()

    session.django_runner.teardown_databases(session.django_db_config)
    session.django_runner.teardown_test_environment()



def truncate(dm):
    """Truncates all tables in all databases in given DatazillaModel."""
    from django.conf import settings
    import MySQLdb
    for sds in dm.sources.values():
        conn = MySQLdb.connect(
            host=sds.datasource.host,
            user=settings.DATAZILLA_DATABASE_USER,
            passwd=settings.DATAZILLA_DATABASE_PASSWORD,
            db=sds.datasource.name,
            )
        cur = conn.cursor()
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("SHOW TABLES")
        for table, in cur.fetchmany():
            cur.execute("TRUNCATE TABLE {0}".format(table))
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.close()



def pytest_funcarg__dm(request):
    """
    A DatazillaModel instance.

    Truncates all tables between tests in order to provide isolation.

    """
    from datazilla.model import DatazillaModel

    dm = DatazillaModel("testproj")
    request.addfinalizer(partial(truncate, dm))
    return dm

