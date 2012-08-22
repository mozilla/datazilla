"""
Tests for management command to create perftest database.

"""
import pytest

from django.core.management import call_command

from datazilla.model import MetricsMethodFactory

from ..model.test_metrics_test_model import setup_pushlog_walk_tests
from ..sample_metric_data import get_metric_collection_data

def call_run_metrics(*args, **kwargs):
    call_command("run_metrics", *args, **kwargs)

def test_no_args(capsys):
    """Shows need for a project or cron_batch."""
    with pytest.raises(SystemExit):
        call_run_metrics()

    exp = (
        "",
        "Error: You must provide either a project or cron_batch value.\n",
        )

    assert capsys.readouterr() == exp

def test_no_numdays(capsys, ptm):

    call_run_metrics(project=ptm.project)

    exp = (
        "Starting for projects: {0}\n".format(ptm.project) +
        "Processing project {0}\n".format(ptm.project) +
        "You must supply the number of days data.\n" +
        "Completed for 1 project(s).\n",
        ""
    )

    assert capsys.readouterr() == exp

def test_bad_numdays(capsys, ptm):

    call_run_metrics(project=ptm.project, numdays="numdays")

    exp = (
        "Starting for projects: {0}\n".format(ptm.project) +
        "Processing project {0}\n".format(ptm.project) +
        "numdays must be an integer.\n" +
        "Completed for 1 project(s).\n",
        ""
        )

    assert capsys.readouterr() == exp

def test_run_metrics_and_summary(capsys, mtm, ptm, plm, monkeypatch):

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    call_run_metrics(
        project=ptm.project,
        pushlog_project='testpushlog',
        numdays=10,
        run_metrics=True,
        summary=True,
        cron_batch='small'
        )

    #Confirm the thresholds set match what is expected
    _test_thresholds(setup_data, mtm, ptm)

    ############
    #The total number of tests passing should be 12,
    #three pages per revision and 4 revisions.  The first
    #revision has no parent and there is no threshold that
    #can be used so it's excluded from the number of passing
    #tests.
    ############
    _test_metric_evaluations(setup_data, mtm, 12)

def test_duplicate_run(capsys, mtm, ptm, plm, monkeypatch):

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    call_run_metrics(
        project=ptm.project,
        pushlog_project='testpushlog',
        numdays=10,
        run_metrics=True,
        summary=True,
        cron_batch='small'
        )

    call_run_metrics(
        project=ptm.project,
        pushlog_project='testpushlog',
        numdays=10,
        run_metrics=True,
        summary=True,
        cron_batch='small'
        )

    #Confirm the thresholds set match what is expected
    _test_thresholds(setup_data, mtm, ptm)

    ############
    #The total number of tests passing should be 15,
    #three pages per revision and 5 revisions.  The first
    #revision that had no parent in the first call_run_metrics pass,
    #now has a threshold to compare to.  The first revision's test
    #values should not be used for threshold storage because it's
    #push date is older than the current threshold.
    ############
    _test_metric_evaluations(setup_data, mtm, 15)

def _test_thresholds(setup_data, mtm, ptm):
    """
    Without modification of setup_data the threshold data should be the
    last sample revision in the setup data revision list.
    """
    last_revision = setup_data['sample_revisions'][
        len(setup_data['sample_revisions']) - 1]

    #Threshold data should point to the last element of sample_revisions
    target_threshold_revision = setup_data['sample_revisions'][
        len(setup_data['sample_revisions']) - 1]

    child_data = mtm.get_test_values(last_revision)

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    for key in child_data:

        threshold_data = mtm.get_threshold_data(child_data[key]['ref_data'])

        threshold_revision = threshold_data[key]['ref_data']['revision']

        assert threshold_revision == target_threshold_revision
        assert threshold_revision != fail_revision
        assert threshold_revision != skip_revision

def _test_metric_evaluations(setup_data, mtm, target_pass_count):
    """
    The metrics data associated with the fail revision should evaluate
    to test failure. All other revisions should evaluate to test success.
    """

    #Test test failure
    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    metric_collection_data = get_metric_collection_data()
    mmf = MetricsMethodFactory(
        metric_collection_data['initialization_data']
        )

    mm = mmf.get_metric_method(setup_data['testsuite_name'])

    metric_fail_count = 0
    metric_pass_count = 0

    metric_summary_fail_count = 0
    metric_summary_pass_count = 0

    for revision in setup_data['sample_revisions']:

        metrics_data = mtm.get_metrics_data(revision)

        if revision == skip_revision:
            #We should have no data for the skip revision
            assert metrics_data == {}
            continue

        for key in metrics_data:

            for data in metrics_data[key]['values']:

                test_result = {}
                test_result[ data['metric_value_name'] ] = data['value']

                if data['metric_value_name'] == 'h0_rejected':
                    metric_evaluation = mm.evaluate_metric_result(
                        test_result
                        )
                    if metric_evaluation == False:
                        metric_fail_count += 1
                        #test evaluation should indicate failure
                        assert revision == fail_revision
                    else:
                        metric_pass_count += 1
                        #all other tests should pass
                        assert revision != fail_revision

                if data['metric_value_name'] == mm.SUMMARY_NAME:

                    summary_evaluation = mm.evaluate_metric_summary_result(
                        test_result
                        )

                    if summary_evaluation == False:
                        metric_summary_fail_count += 1
                        #test evaluation should indicate failure
                        assert revision == fail_revision
                    else:
                        metric_summary_pass_count += 1
                        #all other tests should pass
                        assert revision != fail_revision


    target_fail_count = 3

    assert metric_fail_count == target_fail_count
    assert metric_pass_count == target_pass_count
    assert metric_summary_fail_count == target_fail_count
    assert metric_summary_pass_count == target_pass_count

