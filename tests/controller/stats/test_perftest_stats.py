from decimal import Decimal
import pytest

from django.core.exceptions import FieldError

from ...sample_data import perftest_json
from datazilla.controller.admin.stats import perftest_stats

def test_get_runs_by_branch(ptm):

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

    exp = {
        "Mozilla-Aurora": {
            "count": 1,
            "test_runs": [
                {
                    "status": 1,
                    "date_run": 1330454756,
                    "product": "two",
                    "version": "14.0a2",
                    "branch": "Mozilla-Aurora",
                    "revision": "785345035a3b"
                }
            ]
        }
    }
    runs = perftest_stats.get_runs_by_branch(ptm.project, 1330454756, 1330454756)
    test_run = runs["Mozilla-Aurora"]["test_runs"][0]

    # these ids are auto-incrementing, so we can't rely on the value
    del(test_run["build_id"])
    del(test_run["test_id"])
    del(test_run["machine_id"])
    del(test_run["id"])
    assert runs == exp


def test_get_run_counts_by_branch(ptm):

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
    size = perftest_stats.get_db_size(ptm.project)
    exp = (
        {
            'db_name': u'cam_testproj_objectstore_1',
            'size_mb': Decimal('0.08')
            },
        {
            'db_name': u'cam_testproj_perftest_1',
            'size_mb': Decimal('1.00')
            }

        )
    assert size == exp


def test_get_ref_data_machines(ptm):

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "machines")
    for item in ref_data.itervalues():
        del(item["id"])

    exp = {'qm-pxp01': {'name': 'qm-pxp01'}}
    assert exp == ref_data


def test_get_ref_data_operating_systems(ptm):

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "operating_systems")

    exp = {'linuxUbuntu 11.10': 1L}
    assert exp == ref_data


def test_get_ref_data_options(ptm):

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

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "tests")

    exp = {'Talos tp5r': {'id': 1L, 'name': 'Talos tp5r', 'version': 1L}}

    assert exp == ref_data


def test_get_ref_data_pages(ptm):

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "pages")

    exp = {'one.com': {'id': 2L, 'test_id': 1L, 'url': 'one.com'},
           'three.com': {'id': 1L, 'test_id': 1L, 'url': 'three.com'},
           'two.com': {'id': 3L, 'test_id': 1L, 'url': 'two.com'}}

    assert exp == ref_data


def test_get_ref_data_products(ptm):

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    ref_data = perftest_stats.get_ref_data(ptm.project, "products")

    exp = {'FirefoxMozilla-Aurora14.0a2': 1L}

    assert exp == ref_data


def test_get_ref_data_invalid(ptm):

    ptm.store_test_data(perftest_json())
    ptm.process_objects(1)

    with pytest.raises(FieldError) as e:
        perftest_stats.get_ref_data(ptm.project, "not a valid table name")

    exp = ("FieldError: Not a supported ref_data table.  Must be in: "
        "['tests', 'pages', 'products', 'operating_systems', "
        "'options', 'machines']")

    assert e.exconly() == exp


