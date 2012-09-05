"""
Functions for flexible generation of sample input perftest JSON.

"""
import json
import os

from datazilla.model import utils


def perftest_ref_data_json():
    """Return reference data json structure"""

    file = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "perftest_ref_data.json",
        )

    json_data = ""
    with open(file) as f:
        json_data = f.read()

    return json_data


def perftest_json(**kwargs):
    return json.dumps(perftest_data(**kwargs))


def perftest_data(**kwargs):
    defaults = {
        "results": results(kwargs.pop("results", None)),
        "results_aux": results(kwargs.pop("results_aux", None)),
        "test_build": test_build(**kwargs.pop("test_build", {})),
        "test_machine": test_machine(**kwargs.pop("test_machine", {})),
        "testrun": testrun(**kwargs.pop("testrun", {})),
        }

    defaults.update(kwargs)

    return defaults


def test_machine(**kwargs):
    """Return sample test_machine data structure, with default values."""
    defaults = {
        "name": "qm-pxp01",
        "os": "linux",
        "osversion": "Ubuntu 11.10",
        "platform": "x86_64",
        }

    defaults.update(kwargs)

    return defaults



def testrun_options(**kwargs):
    """Return sample testrun options, with default values."""
    defaults = {
        "responsiveness": "false",
        "rss": "true",
        "shutdown": "true",
        "tpchrome": "true",
        "tpcycles": "3",
        "tpdelay": "",
        "tpmozafterpaint": "false",
        "tppagecycles": "1",
        "tprender": "false",
        }

    defaults.update(kwargs)

    return defaults



def testrun(**kwargs):
    """Return sample testrun, with default values."""
    defaults = {
        "date": "1330454755",
        "options": testrun_options(**kwargs.pop("options", {})),
        "suite": "Talos tp5r",
        }

    defaults.update(kwargs)

    return defaults


test_build_id = 20120228122102


def test_build(**kwargs):
    """Return sample test_build data structure, with default values."""
    global test_build_id

    #build id must be unique for different builds
    test_build_id += 1

    defaults = {
        "branch": "Mozilla-Aurora",
        "id": unicode(test_build_id),
        "name": "Firefox",
        "revision": "785345035a3b",
        "version": "14.0a2"
    }

    defaults.update(kwargs)

    return defaults


def results(results=None):
    """
    Return a sample result data structure, with default values.

    ``results``, if given, should be a dictionary mapping test names to a list
    of result values. The list of result values may be ``None``, in which case
    placeholder values will be used.

    If no ``results`` is given, placeholder results will be returned.

    """
    if results is None:
        results = {
            "one.com": None,
            "two.com": None,
            "three.com": None,
            }

    for result, data in results.items():
        if data is None:
            results[result] = ["789.0", "705.0", "739.0"]

    return results


def create_date_based_data(ptm, monkeypatch, dates=None):
    """Store and process some good and some error blobs on specified dates"""

    if not dates:
        dates = [
            utils.get_day_range(5)["start"],
            utils.get_day_range(4)["start"],
            utils.get_day_range(3)["start"],
            ]

    # 5 days ago
    mocknow = dates[0]
    def mock_now():
        return mocknow
    monkeypatch.setattr(utils, 'get_now_timestamp', mock_now)

    # store the error blob
    blob = perftest_json(
        testrun={"date": dates[0]},
        test_build={"name": "one"},
        )
    badblob = "{0}fooo".format(blob)
    ptm.store_test_data(badblob, error="badness")

    # 4 days ago
    mocknow = dates[1]
    # store the good blobs
    blobs = [
        perftest_json(
            testrun={"date": dates[1]},
            test_build={"name": "one"},
            ),
        perftest_json(
            testrun={"date": dates[1]},
            test_build={"name": "three"},
            ),
        ]

    # 3 days ago
    mocknow = dates[2]

    # store another error blob
    blob = perftest_json(
        testrun={"date": dates[2]},
        test_build={"name": "four"},
        )
    badblob = "{0}fooo".format(blob)
    ptm.store_test_data(badblob, error="Malformed JSON")

    for blob in blobs:
        ptm.store_test_data(blob)

    # now process all of them
    ptm.process_objects(4)


