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
    with pytest.raises(SystemExit):
        call_run_metrics()

    exp = (
        "",
        "Error: You must provide either a project or cron_batch value.\n",
        )

    assert capsys.readouterr() == exp

def test_no_numdays(capsys, ptm, plm):

    call_run_metrics(project=ptm.project, pushlog_project=plm.project)

    exp = (
        "Starting for projects: {0}\n".format(ptm.project) +
        "Processing project {0}\n".format(ptm.project) +
        "You must supply the number of days data.\n" +
        "Completed for 1 project(s).\n",
        ""
    )

    assert capsys.readouterr() == exp

def test_bad_numdays(capsys, ptm, plm):

    call_run_metrics(
        project=ptm.project, pushlog_project=plm.project, numdays="numdays"
        )

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
        pushlog_project=plm.project,
        numdays=10,
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
        pushlog_project=plm.project,
        numdays=10,
        cron_batch='small'
        )

    call_run_metrics(
        project=ptm.project,
        pushlog_project=plm.project,
        numdays=10,
        cron_batch='small'
        )

    #Confirm the thresholds set match what is expected
    _test_thresholds(
        setup_data,
        mtm,
        ptm,
        setup_data['sample_revisions'][0]
        )

    ############
    #The total number of tests passing should be 15,
    #three pages per revision and 5 revisions.  The first
    #revision that had no parent in the first call_run_metrics pass,
    #now has a threshold to compare to.  The first revision's test
    #values should not be used for threshold storage because it's
    #push date is older than the current threshold.
    ############
    _test_metric_evaluations(setup_data, mtm, 15)

    ##########
    #In the absence of a parent if a threshold is available for a
    #particular metrics datum it will be used.
    #
    #After the second pass the first sample revision should have
    #a threshold_test_run_id pointing to the last sample_revision
    ##########
    predicted_threshold_revision = setup_data['sample_revisions'][
        len(setup_data['sample_revisions']) - 1]
    threshold_data = mtm.get_test_values(predicted_threshold_revision)

    no_parent_revision = setup_data['sample_revisions'][0]
    np_data = mtm.get_metrics_data(no_parent_revision)

    for key in np_data:

        threshold_test_run_id = np_data[key]['ref_data']['threshold_test_run_id']

        assert threshold_test_run_id == \
            threshold_data[key]['ref_data']['test_run_id']

def _test_thresholds(setup_data, mtm, ptm, threshold_revision_arg=None):
    """
    Without modification of setup_data the threshold data should be the
    last sample revision in the setup data revision list.
    """
    last_revision = setup_data['sample_revisions'][
        len(setup_data['sample_revisions']) - 1]

    #Threshold data should point to the last element of sample_revisions
    target_threshold_revision = setup_data['sample_revisions'][
        len(setup_data['sample_revisions']) - 1]

    if threshold_revision_arg:
        target_threshold_revision = threshold_revision_arg

    child_data = mtm.get_test_values(last_revision)

    fail_revision = setup_data['fail_revision']
    skip_revision = setup_data['skip_revision']

    for key in child_data:

        threshold_data = mtm.get_threshold_data(child_data[key]['ref_data'])
        threshold_revision = threshold_data[key]['ref_data']['revision']

        assert threshold_revision == target_threshold_revision
        assert threshold_revision != fail_revision
        assert threshold_revision != skip_revision

    #Retrieve test and metric data to confirm threshold_test_run_id chain
    test_fail_index = setup_data['test_fail_index']

    for index, revision in enumerate(setup_data['sample_revisions']):

        if index == 0:
            #first sample will have no parent on the first generation
            #of the metric data
            continue

        if revision == skip_revision:
            continue

        child_metrics_data = mtm.get_metrics_data(revision)

        for mkey in child_metrics_data:

            threshold_test_run_id = child_metrics_data[mkey]['ref_data']['threshold_test_run_id']
            test_run_id = child_metrics_data[mkey]['ref_data']['test_run_id']
            predicted_threshold_id = test_run_id - 1

            if index == (test_fail_index + 1):
                #####
                #   target_threshold_id should always be the last
                #test_run_id, with the exception of the failed test
                #which should not be used as a threshold.
                #   The child push after the fail index should have
                #a threshold_test_run_id pointing to the push before
                #the test failure.
                #####
                predicted_threshold_id = test_run_id - 2

            assert predicted_threshold_id == threshold_test_run_id

def _test_metric_evaluations(setup_data, mtm, target_pass_count):
    """
    The metrics data associated with the fail revision should evaluate
    to test failure. All other revisions should evaluate to test success.
    """

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

