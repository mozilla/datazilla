import json

from datazilla.model import factory

from ...sample_pushlog import get_pushlog_dict_set
from ...sample_data import perftest_data, testrun, perftest_json
from ...sample_metric_data import get_metric_values

from tests.model.test_metrics_test_model import setup_pushlog_walk_tests

from datazilla.controller.admin import testdata
from datazilla.controller.admin.metrics.perftest_metrics import compute_test_run_metrics

def add_test_data(ptm):
    """Add some test runs with filterable values."""
    blobs = [
        perftest_json(
            testrun={"suite": "truth"},
            test_machine={"os": "mac"},
            ),
        perftest_json(
            testrun={"suite": "myth"},
            ),
        perftest_json(
            testrun={"suite": "myth"},
            test_machine={"os": "mac"},
            ),
        perftest_json(
            test_build={"branch": "spam"},
            testrun={"suite": "fact"},
            ),
        perftest_json(
            test_build={"branch": "tactical bacon"},
            testrun={"suite": "fiction"},
            ),
        ]

    for blob in blobs:
        ptm.store_test_data(blob)
    ptm.process_objects(5)


def test_get_testdata_no_filter(ptm, ptrdm, monkeypatch):
    """
    Test getting json blobs for tests by branch and revision

    """

    def mock_ptrdm(project):
        return ptrdm
    monkeypatch.setattr(factory, 'get_ptrdm', mock_ptrdm)

    def mock_ptm(project):
        return ptm
    monkeypatch.setattr(factory, 'get_ptm', mock_ptm)

    add_test_data(ptm)

    result = testdata.get_testdata(
        ptm.project,
        "Mozilla-Aurora",
        "785345035a3b",
        )

    assert len(result) == 3

    suites = [x["testrun"]["suite"] for x in result]
    assert set(suites) == set(["truth", "myth", "myth"])


def test_get_testdata_filter_os_name(ptm, ptrdm, monkeypatch):
    def mock_ptrdm(project):
        return ptrdm
    monkeypatch.setattr(factory, 'get_ptrdm', mock_ptrdm)

    def mock_ptm(project):
        return ptm
    monkeypatch.setattr(factory, 'get_ptm', mock_ptm)

    add_test_data(ptm)

    result = testdata.get_testdata(
        ptm.project,
        "Mozilla-Aurora",
        "785345035a3b",
        os_name="mac"
        )

    assert len(result) == 2

    suites = [x["testrun"]["suite"] for x in result]
    assert set(suites) == set(["truth", "myth"])


def test_get_testdata_filter_test_name(ptm, ptrdm, monkeypatch):
    def mock_ptrdm(project):
        return ptrdm
    monkeypatch.setattr(factory, 'get_ptrdm', mock_ptrdm)

    def mock_ptm(project):
        return ptm
    monkeypatch.setattr(factory, 'get_ptm', mock_ptm)

    add_test_data(ptm)

    result = testdata.get_testdata(
        ptm.project,
        "Mozilla-Aurora",
        "785345035a3b",
        test_name="truth"
    )

    assert len(result) == 1
    assert result[0]["testrun"]["suite"] == "truth"


def test_get_testdata_filter_os_and_test_name(ptm, ptrdm, monkeypatch):

    def mock_ptrdm(project):
        return ptrdm
    monkeypatch.setattr(factory, 'get_ptrdm', mock_ptrdm)

    def mock_ptm(project):
        return ptm
    monkeypatch.setattr(factory, 'get_ptm', mock_ptm)

    add_test_data(ptm)

    result = testdata.get_testdata(
        ptm.project,
        "Mozilla-Aurora",
        "785345035a3b",
        test_name="myth",
        os_name="mac"
    )

    assert len(result) == 1
    assert result[0]["testrun"]["suite"] == "myth"
    assert result[0]["test_machine"]["os"] == "mac"

def test_get_metrics_pushlog(mtm, ptm, plm, monkeypatch ):

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch, True)

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    match_count = 0
    metric_values = get_metric_values()

    revision_index = setup_data['target_revision_index']
    revision = setup_data['sample_revisions'][revision_index]

    metrics_pushlog = testdata.get_metrics_pushlog(
        ptm.project, setup_data['branch'], revision,
        pushlog_project=plm.project, pushes_before=5, pushes_after=5,
        test_name='Talos tp5r'
        )

    for push in metrics_pushlog:

        if push['dz_revision']:

            match_count += 1

            last_index = len(push['revisions']) - 1

            assert push['revisions'][last_index]['revision'] == push['dz_revision']

            for data in push['metrics_data']:
                for page_data in data['pages']:
                    metric_data_keys = data['pages'][page_data].keys()
                    assert metric_values.issubset(metric_data_keys)

    assert match_count == 2


