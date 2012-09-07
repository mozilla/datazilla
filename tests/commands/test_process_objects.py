"""
Tests for management command to process objects.

"""
import pytest
import json
import urllib

from datazilla.model.base import TestData

from ..sample_data import perftest_data
from ..sample_pushlog import pushlog_json, pushlog_json_file

from django.core.management import call_command
from datazilla.model import PerformanceTestModel


def call_process_objects(*args, **kwargs):
    call_command("process_objects", *args, **kwargs)


def test_no_args(capsys):
    """Shows need for a project name."""
    with pytest.raises(SystemExit):
        call_process_objects()

    exp = (
        "",
        "Error: You must provide either a project or cron_batch value.\n",
        )

    assert capsys.readouterr() == exp


def test_successful_populate(monkeypatch, ptm):
    """Successful populate_test_collections."""

    calls = []
    def mock_process(justme, project):
        calls.append(project)
    monkeypatch.setattr(PerformanceTestModel, "process_objects", mock_process)

    call_process_objects(
        project=ptm.project,
        loadlimit=25,
        )

    assert set(calls) == set([25])


def test_object_transfer(ptm, plm, mtm, monkeypatch):

    test_revisions = []

    #Prepare pushlog
    def mock_urlopen(nuttin_honey):
        return pushlog_json_file()
    monkeypatch.setattr(urllib, 'urlopen', mock_urlopen)

    result = plm.store_pushlogs("test_host", 1, branch="Firefox")
    pl = plm.get_branch_pushlog(1)

    fail_index = 3

    #Load objects that match push log entries
    for index, node in enumerate(pl):
        revision = mtm.truncate_revision(node['node'])
        sample_data = TestData( perftest_data(
            test_build={ 'revision': revision,
                         'branch':node['name'] },
            )
        )
        #Simulate test failure for this index
        if index == fail_index:
            data = [50000, 50000, 50000]
            sample_data['results'] = {
                'one.com':data, 'two.com':data, 'three.com':data
                }

        serialized_data = json.dumps( sample_data )
        ptm.store_test_data(serialized_data)

        test_revisions.append(revision)

    #Process the objects
    call_process_objects(
        project=ptm.project,
        pushlog_project=plm.project,
        loadlimit=25,
        )

    trend_keys = set([ 'trend_mean', 'trend_stddev', 'test_evaluation' ])
    extended_keys = set([ 'n_replicates', 'pushlog_id', 'push_date' ])

    #Test resulting metrics
    for index, t_revision in enumerate(test_revisions):
        mdata = mtm.get_metrics_data(t_revision)
        for mkey in mdata:

            metric_value_names = {}

            for value in mdata[mkey]['values']:
                metric_value_names[value['metric_value_name']] = \
                    value['value']

            metric_value_names_set = set( metric_value_names.keys() )

            #All revisions should have extended keys
            assert  metric_value_names_set.issuperset(extended_keys) == True

            #Every revision should have a set of trend keys except for the
            #first which has no parent
            if index == 1:
                assert metric_value_names_set.difference(trend_keys) == \
                    metric_value_names_set
            else:
                assert  metric_value_names_set.issuperset(trend_keys) == \
                    True

                #Every revision should pass except the fail revision
                if index == fail_index:
                    assert metric_value_names['test_evaluation'] == 0
                else:
                    assert metric_value_names['test_evaluation'] == 1


def test_no_load(monkeypatch, ptm):
    """Successful populate_test_collections."""

    calls = []
    def mock_process(justme, loadlimit):
        calls.append(loadlimit)
    monkeypatch.setattr(
        PerformanceTestModel, "process_objects", mock_process
        )

    call_process_objects(
        project=ptm.project,
    )

    assert set(calls) == set([1])
