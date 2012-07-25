import datetime
from contextlib import contextmanager


dataset_num = 1

def create_datasource(model, **kwargs):
    """Utility function to easily create a test DataSource."""
    global dataset_num

    defaults = {
        "project": "foo",
        "dataset": dataset_num,
        "contenttype": "perftest",
        "host": "localhost",
        "type": "MySQL-InnoDB",
        "creation_date": datetime.datetime.now(),
        "cron_batch": "small",
        }

    dataset_num += 1

    defaults.update(kwargs)

    if "name" not in defaults:
        defaults["name"] = "_".join(
            [
                defaults["project"],
                defaults["contenttype"],
                str(defaults["dataset"]),
                ]
            )

    return model.objects.create(**defaults)



@contextmanager
def assert_num_queries(queries):
    from django.db import connection
    _old_debug_cursor = connection.use_debug_cursor
    connection.use_debug_cursor = True
    start_queries = len(connection.queries)
    try:
        yield
        total = len(connection.queries) - start_queries
        msg = "Expected {0} queries, executed {1}".format(queries, total)
        assert total == queries, msg
    finally:
        connection.use_debug_cursor = _old_debug_cursor



def pytest_funcarg__DataSource(request):
    """
    Gives a test access to the DataSource model class.

    """
    from datazilla.model.sql.models import DataSource
    return DataSource



def test_datasources_cached(DataSource):
    """Requesting the full list of DataSources twice only hits the DB once."""
    create_datasource(DataSource)

    DataSource.objects.cached()

    with assert_num_queries(0):
        DataSource.objects.cached()


def test_datasource_cache_invalidated(DataSource):
    """Saving a new datasource invalidates the datasource cache."""
    # prime the cache
    initial = DataSource.objects.cached()

    # create a new datasource
    create_datasource(DataSource)

    # new datasource appears in the list immediately
    assert len(DataSource.objects.cached()) == len(initial) + 1


def test_create_next_dataset(ptm, DataSource):
    """Creating the next dataset keeps all the important fields."""

    sds = ptm.sources["perftest"]
    sds2 = sds.create_next_dataset()

    act = DataSource.objects.filter(dataset=2).values()[0]

    #remove fields we don't want to compare
    del(act["creation_date"])
    del(act["id"])
    del(act["host"])
    del(act["type"])

    exp = {'contenttype': u'perftest',
           'cron_batch': "small",
           'dataset': 2L,
           'name': u'{0}_perftest_2'.format(ptm.project),
           'oauth_consumer_key': None,
           'oauth_consumer_secret': None,
           'project': unicode(ptm.project),
           }

    # special cleanup
    # drop the new database we created
    from django.conf import settings
    import MySQLdb
    conn = MySQLdb.connect(
        host=sds2.datasource.host,
        user=settings.DATAZILLA_DATABASE_USER,
        passwd=settings.DATAZILLA_DATABASE_PASSWORD,
        )
    cur = conn.cursor()
    cur.execute("DROP DATABASE {0}".format(sds2.datasource.name))
    conn.close()

    assert act == exp

