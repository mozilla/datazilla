from ...sample_data import perftest_json
from datazilla.controller.admin.stats import perftest_stats

import json

def test_get_runs_by_branch(ptm, ptsm, monkeypatch):

    def mock_ptsm(project):
        return ptsm
    monkeypatch.setattr(perftest_stats, 'ptsm', mock_ptsm)

    blobs = [
        perftest_json(
            testrun={"date": "1330454755"},
            test_build={"name": "one"},
            ),
        perftest_json(
            testrun={"date": "1330454756"},
            test_build={"name": "two"},
            ),
        perftest_json(
            testrun={"date": "1330454758"},
            test_build={"name": "three"},
            ),
        ]

    for blob in blobs:
        ptm.store_test_data(blob)
    ptm.process_objects(3)

    runs = perftest_stats.get_runs_by_branch("talos", 1330454757, 1660454757)
    assert False, json.dumps(runs, indent=4)


def test_get_ref_data():
    raise NotImplementedError


def test_get_ref_data_method():
    raise NotImplementedError

