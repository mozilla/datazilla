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

    from django.conf import settings
    from django.test.simple import DjangoTestSuiteRunner
    # we don't actually let Django run the tests, but we need to use some
    # methods of its runner for setup/teardown of dbs and some other things
    session.django_runner = DjangoTestSuiteRunner()
    # this provides templates-rendered debugging info and locmem mail storage
    session.django_runner.setup_test_environment()
    # support custom db prefix for tests for the main datazilla datasource
    # as well as for the testproj and testpushlog dbs
    prefix = getattr(settings, "TEST_DB_PREFIX", "")
    settings.DATABASES["default"]["TEST_NAME"] = "{0}test_datazilla".format(prefix)
    # this sets up a clean test-only database
    session.django_db_config = session.django_runner.setup_databases()
    # store the name of the test project/pushlog based on user custom settings
    session.perftest_name = "{0}testproj".format(prefix)
    session.pushlog_name = "{0}testpushlog".format(prefix)

    increment_cache_key_prefix()

    from datazilla.model import PerformanceTestModel, PushLogModel
    ptm = PerformanceTestModel.create(
        session.perftest_name,
        cron_batch="small",
        )
    PushLogModel.create(project=session.pushlog_name)

    # patch in additional test-only procs on the datasources
    objstore = ptm.sources["objectstore"]
    del objstore.dhub.procs[objstore.datasource.key]
    objstore.dhub.data_sources[objstore.datasource.key]["procs"].append(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "objectstore_test.json",
            )
        )
    objstore.dhub.load_procs(objstore.datasource.key)

    perftest = ptm.sources["perftest"]
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

    source_list = PerformanceTestModel(session.perftest_name).sources.values()
    source_list.extend(PushLogModel(project=session.pushlog_name).sources.values())
#    return

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
    test PerformanceTestModel database.

    """
    from django.test.testcases import restore_transaction_methods
    from django.db import transaction
    from datazilla.model import PerformanceTestModel
#    return

    restore_transaction_methods()
    transaction.rollback()
    transaction.leave_transaction_management()

    ptm = PerformanceTestModel(item.session.perftest_name)
    truncate(ptm, set(['metric', 'metric_value']))



def truncate(ptm, skip_list=None):
    """
    Truncate all tables in all databases in given DatazillaModelBase.

    skip_list is a list of table names to skip truncation.
    """
    ptm.disconnect()

    skip_list = set(skip_list or [])
    from django.conf import settings
    import MySQLdb
    for sds in ptm.sources.values():
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
                # needed to use backticks around table name, because if the
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


def pytest_funcarg__ptm(request):
    """
    Give a test access to a PerformanceTestModel instance.

    """
    from datazilla.model import PerformanceTestModel

    ptm = PerformanceTestModel(request._pyfuncitem.session.perftest_name)
    request.addfinalizer(partial(truncate, ptm, ["metric", "metric_value"]))


    return ptm


def pytest_funcarg__plm(request):
    """
    Give a test access to a PushLogModel instance.

    Truncate all project tables between tests in order to provide isolation.

    """
    from datazilla.model import PushLogModel

    plm = PushLogModel(
        request._pyfuncitem.session.pushlog_name,
        out=sys.stdout, verbosity=2)

    request.addfinalizer(partial(truncate, plm, ["branches"]))
    return plm

def pytest_funcarg__mtm(request):
    """
    Give a test access to a MetricsTestModel instance.

    """
    from datazilla.model.metrics import MetricsTestModel

    mtm = MetricsTestModel(request._pyfuncitem.session.perftest_name)
    request.addfinalizer(partial(truncate, mtm, ["metric", "metric_value"]))
    return mtm

def pytest_funcarg__ptsm(request):
    """
    Give a test access to a PerformanceTestStatsModel instance.

    """
    from datazilla.model.stats import PerformanceTestStatsModel

    return PerformanceTestStatsModel(request._pyfuncitem.session.perftest_name)


def pytest_funcarg__plsm(request):
    """
    Give a test access to a PushLogStatsModel instance.

    Truncate all project tables between tests in order to provide isolation.

    """
    from datazilla.model.stats import PushLogStatsModel

    plsm = PushLogStatsModel(
        request._pyfuncitem.session.pushlog_name)

    request.addfinalizer(partial(truncate, plsm, ["branches"]))
    return plsm
