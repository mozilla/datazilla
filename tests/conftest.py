from functools import partial
import os
import sys

from datazilla.vendor import add_vendor_lib



def pytest_sessionstart(session):
    """
    Set up the test environment.

    Set DJANGO_SETTINGS_MODULE, adds the vendor lib, and sets up a test
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

    increment_cache_key_prefix()

    from datazilla.model import PerformanceTestModel, PushLogModel
    dm = PerformanceTestModel.create("testproj")
    PushLogModel.create(project="testpushlog")

    # patch in additional test-only procs on the datasources
    objstore = dm.sources["objectstore"]
    del objstore.dhub.procs[objstore.datasource.key]
    objstore.dhub.data_sources[objstore.datasource.key]["procs"].append(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "objectstore_test.json",
            )
        )
    objstore.dhub.load_procs(objstore.datasource.key)

    perftest = dm.sources["perftest"]
    del perftest.dhub.procs[perftest.datasource.key]
    perftest.dhub.data_sources[perftest.datasource.key]["procs"].append(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "perftest_test.json",
            )
        )
    perftest.dhub.load_procs(perftest.datasource.key)



def pytest_sessionfinish(session):
    """Tear down the test environment, including databases."""
    print("\n")

    from django.conf import settings
    from datazilla.model import PerformanceTestModel, PushLogModel
    import MySQLdb

    source_list = PerformanceTestModel("testproj").sources.values()
    source_list.extend(PushLogModel(project="testpushlog").sources.values())
    for sds in source_list:
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



def pytest_runtest_setup(item):
    """
    Per-test setup.

    Start a transaction and disable transaction methods for the duration of the
    test. The transaction will be rolled back after the test. This prevents any
    database changes made to Django ORM models from persisting between tests,
    providing test isolation.

    Also clear the cache (by incrementing the key prefix).

    """
    from django.test.testcases import disable_transaction_methods
    from django.db import transaction

    transaction.enter_transaction_management()
    transaction.managed(True)
    disable_transaction_methods()

    increment_cache_key_prefix()



def pytest_runtest_teardown(item):
    """
    Per-test teardown.

    Roll back the Django ORM transaction and truncates tables in the
    "testproj" PerformanceTestModel.

    """
    from django.test.testcases import restore_transaction_methods
    from django.db import transaction
    from datazilla.model import PerformanceTestModel

    restore_transaction_methods()
    transaction.rollback()
    transaction.leave_transaction_management()

    ptm = PerformanceTestModel("testproj")
    truncate(ptm)



def truncate(dm, skip_list=None):
    """
    Truncate all tables in all databases in given DatazillaModelBase.

    skip_list is a list of table names to skip truncation.
    """
    dm.disconnect()

    skip_list = set(skip_list or [])

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

        for table, in cur.fetchall():
            # if there is a skip_list, then skip any table with matching name
            if table.lower() not in skip_list:
                # needed to us backticks around table name, because if the
                # table name is a keyword (like "option") then this will fail
                cur.execute("TRUNCATE TABLE `{0}`".format(table))

        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.close()


def increment_cache_key_prefix():
    """Increment a cache prefix to effectively clear the cache."""
    from django.core.cache import cache
    cache.key_prefix = ""
    prefix_counter_cache_key = "datazilla-tests-key-prefix-counter"
    try:
        key_prefix_counter = cache.incr(prefix_counter_cache_key)
    except ValueError:
        key_prefix_counter = 0
        cache.set(prefix_counter_cache_key, key_prefix_counter)
    cache.key_prefix = "t{0}".format(key_prefix_counter)


def pytest_funcarg__dm(request):
    """
    Give a test access to a PerformanceTestModel instance.

    """
    from datazilla.model import PerformanceTestModel

    return PerformanceTestModel("testproj")


def pytest_funcarg__plm(request):
    """
    Give a test access to a PushLogModel instance.

    Truncate all project tables between tests in order to provide isolation.

    """
    from datazilla.model import PushLogModel

    plm = PushLogModel("testpushlog", out=sys.stdout, verbosity=2)

    request.addfinalizer(partial(truncate, plm, ["branches"]))
    return plm
