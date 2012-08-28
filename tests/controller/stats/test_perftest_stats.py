from ...sample_data import perftest_json
from datazilla.controller.admin.stats import perftest_stats

def test_get_runs_by_branch(ptsm, monkeypatch):

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
        ptsm.store_test_data(blob)
    ptsm.process_objects(3)

    runs = perftest_stats.get_runs_by_branch("talos", 1330454756, 1660454756)
    assert False, runs


def test_get_ref_data():
    raise NotImplementedError


def test_get_ref_data_method():
    raise NotImplementedError

