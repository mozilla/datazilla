from decimal import Decimal
import pytest

from django.core.exceptions import FieldError

from datazilla.model import factory
from ...sample_data import perftest_json
from datazilla.controller.admin.stats import perftest_stats

def test_get_runs_by_branch(ptm, plm, monkeypatch):
    """
    Test get_runs_by_branch method.
    """
    def mock_plm():
        return plm
    monkeypatch.setattr(factory, 'get_plm', mock_plm)
    # don't need to monkeypatch the ptsm, because we pass the project
    # name in for use in its construction.

    blobs = [
        perftest_json(
            testrun={"date": 1330454755},
            test_build={"name": "one"},
            ),
        perftest_json(
            testrun={"date": 1330454756},
            test_build={"name": "two"},
            ),
        perftest_json(
            testrun={"date": 1330454758},
            test_build={"name": "three"},
            ),
        ]

    for blob in blobs:
        ptm.store_test_data(blob)
    ptm.process_objects(3)

    exp_run = {
        "status": 1,
        "date_run": 1330454756,
        "product": "two",
        "version": "14.0a2",
        "branch": "Mozilla-Aurora",
        "revision": "785345035a3b"
        }

    runs = perftest_stats.get_runs_by_branch(ptm.project, 1330454756, 1330454756)

    assert runs["Mozilla-Aurora"]["count"] == 1
    assert runs["Mozilla-Aurora"]["test_runs"][0] == exp_run


def test_get_sssruns_by_branch_past_limit(ptm, plm, monkeypatch):
    """
    Test get_runs_by_branch method exceeding the 80 count limit.

    Since the limit per branch is 80, create more than 80 items to test that.
    """

    def mock_plm():
        return plm
    monkeypatch.setattr(factory, 'get_plm', mock_plm)

    for i in range(81):
        blob = perftest_json(
            testrun={"date": 1330454756},
            test_build={"name": "testname{0}".format(i)}
            )
        ptm.store_test_data(blob)
    ptm.process_objects(81)

    runs = perftest_stats.get_runs_by_branch(ptm.project, 1330454756, 1330454756)

    assert runs["Mozilla-Aurora"]["limit"] == 80
    assert runs["Mozilla-Aurora"]["count"] == 80
    assert runs["Mozilla-Aurora"]["total_count"] == 81


def test_get_run_counts_by_branch(ptm):
    """Test get_run_counts_by_branch method."""

    blobs = [
        perftest_json(
            testrun={"date": 1330454755},
            test_build={"name": "one"},
            ),
        perftest_json(
            testrun={"date": 1330454756},
            test_build={"name": "two"},
            ),
        perftest_json(
            testrun={"date": 1330454758},
            test_build={"name": "three"},
            ),
        ]

    for blob in blobs:
        ptm.store_test_data(blob)
    ptm.process_objects(3)

    exp = {'Mozilla-Aurora': {'count': 1L}}
    runs = perftest_stats.get_run_counts_by_branch(
        ptm.project,
        1330454756,
        1330454756,
        )
    assert runs == exp


def test_get_db_size(ptm):
    """Test the get_db_size method."""
    sizes = perftest_stats.get_db_size(ptm.project)

    db_names = [x["db_name"] for x in sizes]
    exp_db_names = [
        u'{0}_objectstore_1'.format(ptm.project),
        u'{0}_perftest_1'.format(ptm.project),
        ]
    assert set(db_names) == set(exp_db_names)

    for db in sizes:
        assert db["size_mb"] > 0


def test_get_ref_data_machines(ptm):
    """Test get_ref_data method to get machines list."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "machines")
    for item in ref_data.itervalues():
        del(item["id"])

    exp = {'qm-pxp01': {'name': 'qm-pxp01'}}
    assert exp == ref_data


def test_get_ref_data_operating_systems(ptm):
    """Test get_ref_data method to get operating systems list."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "operating_systems")

    exp = {'linuxUbuntu 11.10': 1L}
    assert exp == ref_data


def test_get_ref_data_options(ptm):
    """Test get_ref_data method to get options list."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "options")

    exp = {'responsiveness': {'id': 1L, 'name': 'responsiveness'},
           'rss': {'id': 9L, 'name': 'rss'},
           'shutdown': {'id': 8L, 'name': 'shutdown'},
           'tpchrome': {'id': 4L, 'name': 'tpchrome'},
           'tpcycles': {'id': 6L, 'name': 'tpcycles'},
           'tpdelay': {'id': 3L, 'name': 'tpdelay'},
           'tpmozafterpaint': {'id': 2L, 'name': 'tpmozafterpaint'},
           'tppagecycles': {'id': 5L, 'name': 'tppagecycles'},
           'tprender': {'id': 7L, 'name': 'tprender'}}

    assert exp == ref_data


def test_get_ref_data_tests(ptm):
    """Test get_ref_data method to get tests list."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "tests")

    exp = {'Talos tp5r': {'id': 1L, 'name': 'Talos tp5r', 'version': 1L}}

    assert exp == ref_data


def test_get_ref_data_pages(ptm):
    """Test get_ref_data method to get pages list."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "pages")

    exp = {'one.com': {'id': 2L, 'test_id': 1L, 'url': 'one.com'},
           'three.com': {'id': 1L, 'test_id': 1L, 'url': 'three.com'},
           'two.com': {'id': 3L, 'test_id': 1L, 'url': 'two.com'}}

    assert exp == ref_data


def test_get_ref_data_products(ptm):
    """Test get_ref_data method to get products list."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "products")

    exp = {'FirefoxMozilla-Aurora14.0a2': 1L}

    assert exp == ref_data


def test_get_ref_data_invalid(ptm):
    """Test get_ref_data method with an invalid key."""

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    with pytest.raises(FieldError) as e:
        perftest_stats.get_ref_data(ptm.project, "not a valid table name")

    exp = ("FieldError: Not a supported ref_data table.  Must be in: "
        "['tests', 'pages', 'products', 'operating_systems', "
        "'options', 'machines']")

    assert e.exconly() == exp


