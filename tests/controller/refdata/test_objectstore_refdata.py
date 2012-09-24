from decimal import Decimal

from datazilla.model.utils import get_day_range
from ...sample_data import perftest_json
from datazilla.controller.admin.refdata import objectstore_refdata

def store_and_process_2_good_2_error_blobs(ptm):
    """Store 2 good blobs, and 2 that are marked as having an error"""

    # store the error blob
    blob = perftest_json(
        testrun={"date": 1330454756},
        test_build={"name": "one"},
        )
    badblob = "{0}fooo".format(blob)
    ptm.store_test_data(badblob, error="badness")

    blob = perftest_json(
        testrun={"date": 1330454756},
        test_build={"name": "four"},
        )
    badblob = "{0}fooo".format(blob)
    ptm.store_test_data(badblob, error="Malformed JSON")

    # store the good blobs
    blobs = [
        perftest_json(
            testrun={"date": 1330454755},
            test_build={"name": "one"},
            ),
        perftest_json(
            testrun={"date": 1330454758},
            test_build={"name": "three"},
            ),
        ]

    for blob in blobs:
        ptm.store_test_data(blob)

    # now process all of them
    ptm.process_objects(4)


def test_get_error_count(ptm):
    """Test the get_error_count method."""

    store_and_process_2_good_2_error_blobs(ptm)
    date_range = get_day_range(1)
    result = objectstore_refdata.get_error_count(
        ptm.project,
        date_range["start"],
        date_range["stop"],
        )
    exp = (
        {'count': 1L, 'message': u'Malformed JSON'},
        {'count': 1L, 'message': u'Other'},
        )
    assert result == exp


def test_get_error_list(ptm):
    """Test the get_error_list method."""

    store_and_process_2_good_2_error_blobs(ptm)
    date_range = get_day_range(1)
    result = objectstore_refdata.get_error_list(
        ptm.project,
        date_range["start"],
        date_range["stop"],
        )
    exp = (
        {
            'id': 1L,
            'test_run_id': None,
            'worker_id': None,
            'processed_flag': u'ready',
            'error_msg': u'badness'
            },
        {
            'id': 2L,
            'test_run_id': None,
            'worker_id': None,
            'processed_flag': u'ready',
            'error_msg': u'Malformed JSON',
            })

    #we don't want to compare the date loaded
    for item in result:
        del(item["date_loaded"])

    assert result == exp


def test_get_json_blob(ptm):
    """Test get_json_blob method"""

    blob = perftest_json(
        testrun={"date": 1330454756},
        test_build={"name": "one"},
        )
    badblob = "fooo{0}".format(blob)
    ptm.store_test_data(badblob, error="badness")

    result = objectstore_refdata.get_json_blob(ptm.project, 1)

    assert badblob == result


def test_get_json_blob_bad_id(ptm):
    """Test get_json_blob method with a non-existent id."""
    blob = perftest_json(
        testrun={"date": 1330454756},
        test_build={"name": "one"},
        )
    badblob = "fooo{0}".format(blob)
    ptm.store_test_data(badblob, error="badness")

    result = objectstore_refdata.get_json_blob(ptm.project, 10)

    assert not result


def test_get_error_detail_count(ptm):
    """Test get_error_detail_count method."""

    store_and_process_2_good_2_error_blobs(ptm)
    date_range = get_day_range(1)
    result = objectstore_refdata.get_error_detail_count(
        ptm.project,
        date_range["start"],
        date_range["stop"],
        )
    exp = {
        'four - Mozilla-Aurora - 14.0a2': 1,
        'one - Mozilla-Aurora - 14.0a2': 1,
        }

    assert result == exp


def test_result_key_invalid_value():
    """Test get_result_key with an invalid key."""
    result = objectstore_refdata.result_key({"mango": "food"})
    assert result == "unknown"


def test_get_db_size(ptm):
    """Test the get_db_size method."""
    sizes = objectstore_refdata.get_db_size(ptm.project)

    db_names = [x["db_name"] for x in sizes]
    exp_db_names = [
        u'{0}_objectstore_1'.format(ptm.project),
        u'{0}_perftest_1'.format(ptm.project),
        ]
    assert set(db_names) == set(exp_db_names)

    for db in sizes:
        assert db["size_mb"] > 0

