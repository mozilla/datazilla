import json
import datetime
import copy
import urllib
import time

from datazilla.model.base import TestData

from ..sample_data import perftest_data
from ..sample_pushlog import get_pushlog_json_set, get_pushlog_json_readable

from ..sample_metric_data import (
    get_metrics_key_data, get_metrics_summary_key_data,
    get_metric_collection_data, get_sample_p_values,
    get_metric_sample_data_summary, get_metric_sample_data,
    get_sample_ref_data, get_sample_ttest_data )

from datazilla.controller.admin.metrics.perftest_metrics import compute_test_run_metrics


def test_metric_keys(mtm):

    data = get_metrics_key_data()

    reference_set = set(data['key_data'].keys())

    model_set = set(mtm.METRIC_KEYS)

    assert reference_set == model_set

def test_metric_summary_keys(mtm):

    data = get_metrics_summary_key_data()

    reference_set = set(data['key_data'].keys())

    model_set = set(mtm.METRIC_SUMMARY_KEYS)

    assert reference_set == model_set

def test_get_metrics_key_value(mtm):

    data = get_metrics_key_data(key_delimiter=mtm.KEY_DELIMITER)

    key = mtm.get_metrics_key( data['key_data'] )

    assert data['default_value'] == key

def test_get_metrics_summary_key_value(mtm):

    data = get_metrics_summary_key_data(
        key_delimiter=mtm.KEY_DELIMITER
        )

    key = mtm.get_metrics_summary_key( data['key_data'] )

    assert data['default_value'] == key

def test_extend_with_metrics_keys(mtm):

    key_data = get_metrics_key_data()

    reference_data = copy.copy(key_data['key_data'])

    reference_data['test_run_id'] = None
    reference_data['test_name'] = None

    test_data= {}
    test_data['test_run_id'] = 100
    test_data['test_name'] = 'yet another test'

    model_data = mtm.extend_with_metrics_keys(
        test_data, ['test_run_id', 'test_name']
        )

    reference_set = set(reference_data.keys())
    model_set = set(model_data.keys())

    assert  reference_set == model_set
    #make sure we extended model_data with test_run_id
    #and test_name
    assert test_data['test_run_id'] == model_data['test_run_id']
    assert test_data['test_name'] == model_data['test_name']

def test_truncate_revision(mtm):

    reference_data = 'asdf781435quhafo8qy3lrhaos8eyajkwwehfqywralisudyf9a'

    revision = mtm.truncate_revision(reference_data)

    assert len(revision) == mtm.REVISION_CHAR_COUNT
    #revision should start at beginning of reference_data
    assert 0 == reference_data.find(revision)

def test_add_skip_revision(mtm):

    revision = 'asdf781435qu'

    mtm.add_skip_revision(revision)

    reference_data = set([revision])

    assert reference_data == mtm.skip_revisions

def test_get_metric_summary_name():

    metrics_reference_data = get_metric_collection_data()

    from datazilla.model import MetricsTestModel

    mtm = MetricsTestModel(
        'talos', metrics_reference_data['initialization_data']
        )
    name = mtm.get_metric_summary_name(
        metrics_reference_data['testsuite_name']
        )

    assert metrics_reference_data['metric_summary_name'] == name

def test_get_test_values_mk(ptm, mtm):

    sample_data = TestData(perftest_data())

    ptm.load_test_data(sample_data)

    revision = sample_data['test_build']['revision']
    model_data = mtm.get_test_values_by_revision(revision)

    examine_metric_key_lookup(mtm, sample_data, model_data)

def test_get_test_values(mtm, ptm):

    sample_data = TestData(perftest_data())

    sample_revision = sample_data['test_build']['revision']

    ptm.load_test_data(sample_data)

    model_data = mtm.get_test_values_by_revision(sample_revision)

    examine_metric_key_lookup(mtm, sample_data, model_data)

def test_get_threshold_data(ptm, mtm):

    child_sample_data = TestData( perftest_data())
    child_revision = child_sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'

    parent_sample_data = TestData(
        perftest_data(test_build={ 'revision': parent_revision })
        )

    ref_data = get_sample_ref_data()

    #We need to load some data so the foreign
    #key constraints for the reference data are
    #valid
    ptm.load_test_data(parent_sample_data)
    ptm.load_test_data(child_sample_data)

    sample_ttest_data = get_sample_ttest_data()

    #The sample data ttest passes with itself this
    #causes the data to be stored as threshold data
    mtm.store_metric_results(child_revision, ref_data, sample_ttest_data, 1)

    threshold_data = mtm.get_threshold_data(ref_data)
    mkey = threshold_data.keys()[0]

    for k in mtm.METRIC_KEYS:
        assert threshold_data[mkey]['ref_data'][k] == ref_data[k]

def test_run_metric_method(mtm, ptm):

    #Get sample data
    child_sample_data = TestData(perftest_data())
    parent_sample_data = TestData(perftest_data())

    #Get sample reference data
    ref_data = get_sample_ref_data()

    for key in child_sample_data['results']:
        reference_results = get_metric_sample_data(
            key, child_sample_data
            )

        child_values = child_sample_data['results'][key]
        parent_values = parent_sample_data['results'][key]

        #Run metric method
        results = mtm.run_metric_method(
            ref_data, child_values, parent_values
            )

        for data_key in reference_results:

            assert results[data_key] == reference_results[data_key]

def test_run_metric_summary(mtm, ptm):

    #Get sample data
    child_sample_data = TestData(perftest_data())
    test_name = child_sample_data['testrun']['suite']

    #Get sample reference data
    ref_data = get_sample_ref_data()
    reference_results = get_metric_sample_data_summary()

    values = get_sample_p_values()
    model_results = mtm.run_metric_summary(ref_data, values['db_struct'])

    #results from fdr.rejector are stored in a key/value pair where
    #the key is status and value is a list of booleans associated
    #with each p value supplied.  model_results and reference_results
    #should match
    for d, m in zip( reference_results['status'], model_results ):

        assert m['value'] == d
        assert m['metric_value_name'] == mtm.get_metric_summary_name(
            test_name
            )

def test_store_metric_summary_results(mtm, ptm):

    ######
    #This is a functional test that executes all operations
    #through metric summary storage and then confirms that the
    #metric summary data stored matches the the summary data
    #generated.
    ######

    #Get sample data
    child_sample_data = TestData(perftest_data())

    test_name = child_sample_data['testrun']['suite']
    child_revision = child_sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'

    parent_sample_data = TestData(
        perftest_data(test_build={ 'revision': parent_revision })
        )

    ptm.load_test_data(parent_sample_data)
    ptm.load_test_data(child_sample_data)

    parent_keys = parent_sample_data['results'].keys()
    n_replicates = len( parent_sample_data['results'][ parent_keys[0] ] )

    child_data = mtm.get_test_values_by_revision(child_revision)
    parent_data = mtm.get_test_values_by_revision(parent_revision)

    summary_name = mtm.get_metric_summary_name(test_name)

    for key in child_data:

        #Run metric method
        results = mtm.run_metric_method(
            child_data[key]['ref_data'],
            child_data[key]['values'],
            parent_data[key]['values']
            )

        #Store the results
        mtm.store_metric_results(
            child_revision,
            child_data[key]['ref_data'],
            results,
            parent_data[key]['ref_data']['test_run_id']
            )

        #Retrieve the metric data
        metrics_data = mtm.get_metrics_data(child_revision)

        #Compute the metric summary
        summary_results = mtm.run_metric_summary(
            metrics_data[key]['ref_data'], metrics_data[key]['values']
            )

        metrics_data[key]['ref_data']['pushlog_id'] = 1
        metrics_data[key]['ref_data']['push_date'] = 1
        metrics_data[key]['ref_data']['n_replicates'] = n_replicates

        #Store the metric summary results
        mtm.store_metric_summary_results(
            child_revision,
            metrics_data[key]['ref_data'],
            summary_results,
            metrics_data[key]['values'],
            parent_data[key]['ref_data']['test_run_id']
            )

        #Metric data should contain the summary results
        summary_metrics_data = mtm.get_metrics_data(child_revision)

        for data in summary_metrics_data[key]['values']:
            if data['metric_value_name'] == summary_name:
                #We should find the computed summary data in
                #the data retrieved
                assert summary_results[0]['page_id'] == data['page_id']
                assert summary_results[0]['value'] == data['value']


def test_store_metric_results(mtm, ptm):

    child_sample_data = TestData(perftest_data())
    child_revision = child_sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'

    parent_sample_data = TestData(
        perftest_data(test_build={ 'revision': parent_revision })
        )

    ref_data = get_sample_ref_data()

    #We need to load some data so the foreign
    #key constraints for the reference data are
    #valid
    ptm.load_test_data(parent_sample_data)
    ptm.load_test_data(child_sample_data)

    sample_ttest_data = get_sample_ttest_data()

    mtm.store_metric_results(child_revision, ref_data, sample_ttest_data, 1)

    metric_data_reference = ptm.sources["perftest"].dhub.execute(
        proc="perftest.selects.get_computed_metrics",
        placeholders=[child_revision])

    adapted_reference = _adapt_data(mtm, metric_data_reference)

    child_data = mtm.get_metrics_data(child_revision)

    reference_keys = adapted_reference.keys()
    data_keys = child_data.keys()

    #Confirm the metric keys match the reference
    assert data_keys == reference_keys

    for key in reference_keys:
        #Confirm the values match the reference
        assert child_data[key]['values'] == adapted_reference[key]['values']


def test_insert_or_update_metric_threshold(mtm, ptm):

    # get sample data
    sample_data = TestData(
        perftest_data(results={'one.com':[10,20,30,40]})
        )

    test_name = sample_data['testrun']['suite']
    revision = sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'
    parent_sample_data = TestData( perftest_data(
        test_build={ 'revision': parent_revision },
        results={'one.com':[1,2,3,4]}
        )
    )

    # load sample data
    ptm.load_test_data(parent_sample_data)
    ptm.load_test_data(sample_data)

    # retrieve loaded test values
    parent_model_data = mtm.get_test_values_by_revision(parent_revision)
    model_data = mtm.get_test_values_by_revision(revision)

    # retrieve metric id for insert_or_update_threshold
    metric_method = mtm.mf.get_metric_method(test_name)
    metric_id = metric_method.get_metric_id()

    for key in model_data:

        #First pass should be inserting not updating
        mtm.insert_or_update_metric_threshold(
            revision, model_data[key]['ref_data'],
            metric_id
            )

        inserted_threshold_data = mtm.get_threshold_data(
            model_data[key]['ref_data']
            )

        #We should get the model_data back here
        assert model_data[key]['values'] == \
            inserted_threshold_data[key]['values']

    for key in parent_model_data:

        #Second pass should be updating not inserting
        mtm.insert_or_update_metric_threshold(
            parent_revision, parent_model_data[key]['ref_data'],
            metric_id
            )
        #use child ref data to retrieve thresholds
        updated_threshold_data = mtm.get_threshold_data(
            model_data[key]['ref_data']
            )

        #thresholds should point to the parent now
        assert parent_model_data[key]['values'] == \
            updated_threshold_data[key]['values']

        #parent model data will have a test_run_id of 1 since it's the
        #first one inserted, this should now be the test_run_id associated
        #with the threshold data
        assert 1 == updated_threshold_data[key]['ref_data']['test_run_id']

def test_get_parent_test_data_case_one(mtm, ptm, plm, monkeypatch):

    #######
    # Functional test for get_parent_test_data use case
    #
    # TEST CASE 1: If no child data is supplied the parent push should be
    # sample_revisions[ target_revision_index - 1]
    #######

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    sample_revisions = setup_data['sample_revisions']

    #Get the child data
    test_one_data = mtm.get_test_values_by_revision(
        sample_revisions[setup_data['target_revision_index']]
        )

    #Retrieve child metric key
    test_one_key = test_one_data.keys()[0]

    parent_data, results = mtm.get_parent_test_data(
        setup_data['branch_pushlog'],
        setup_data['target_revision_index'],
        test_one_key, None
        )

    #Parent data should be at target_revision_index - 1
    reference_data = mtm.get_test_values_by_revision(
        sample_revisions[setup_data['target_revision_index'] - 1]
        )

    assert parent_data['ref_data'] == \
        reference_data[test_one_key]['ref_data']

def test_get_parent_test_data_case_two(mtm, ptm, plm, monkeypatch):

    #######
    # Functional test for get_parent_test_data use case
    #
    # TEST CASE 2: skip_index should have no data in perftest and should
    #   not be selected as a parent.  The parent should be the sample
    #   revision before the skipped index.  So setup_data['skip_index'] - 1
    #######

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    skip_revision = setup_data['skip_revision']
    child_revision = setup_data['sample_revisions'][
        setup_data['skip_index'] + 1 ]
    #parent target should be before the skipped revision
    target_revision = setup_data['sample_revisions'][
        setup_data['skip_index'] - 1 ]

    #Get the child data
    test_two_data = mtm.get_test_values_by_revision(child_revision)

    test_two_key = test_two_data.keys()[0]

    parent_data, results = mtm.get_parent_test_data(
        setup_data['branch_pushlog'],
        setup_data['skip_index'] + 1,
        test_two_key, None
        )

    reference_data = mtm.get_test_values_by_revision(target_revision)

    assert mtm.skip_revisions == set([skip_revision])
    assert parent_data['ref_data'] == \
        reference_data[test_two_key]['ref_data']

def test_get_parent_test_data_case_three(mtm, ptm, plm, monkeypatch):

    #########
    # Functional test for get_parent_test_data use case
    #
    # TEST CASE 3: When metric_method_data is provided the metric test is
    #   required to pass for a push to be a valid parent.  The fail_revision
    #   in setup_data has sample data with artificially high test value
    #   results that should cause the ttest to fail and the revision to be
    #   passed over when storing threshold data.  No parent should be found
    #   for the fail revision if the fail data is supplied to
    #   get_parent_test_data.
    #########
    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    fail_revision = setup_data['fail_revision']
    fail_index = setup_data['test_fail_index']

    fail_data = mtm.get_test_values_by_revision(fail_revision)

    for key in fail_data:

        parent_data, results = mtm.get_parent_test_data(
            setup_data['branch_pushlog'],
            fail_index,
            key,
            fail_data[key]['values']
            )

        assert parent_data == {}

        threshold_data = mtm.get_threshold_data(fail_data[key]['ref_data'])

        assert threshold_data == {}

def test_get_parent_test_data_case_four(mtm, ptm, plm, monkeypatch):

    #########
    # Functional test for get_parent_test_data use case
    #
    # TEST CASE 4: When metric_method_data is provided the metric test is
    #   required to pass for a push to be a valid parent.  This test
    #   provides child data that is the same as the parent.  So the ttest
    #   should pass and the parent should be the first push found.
    #   So sample_revisions[ target_revision_index - 1] should be the
    #   parent.
    #########
    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    sample_revisions = setup_data['sample_revisions']

    #Get the child data
    test_four_data = mtm.get_test_values_by_revision(
        sample_revisions[setup_data['target_revision_index']]
        )

    #Retrieve child metric key
    test_four_key = test_four_data.keys()[0]

    parent_data, results = mtm.get_parent_test_data(
        setup_data['branch_pushlog'],
        setup_data['target_revision_index'],
        test_four_key,
        test_four_data[test_four_key]['values']
        )

    #Parent data should be at target_revision_index - 1
    reference_data = mtm.get_test_values_by_revision(
        sample_revisions[setup_data['target_revision_index'] - 1]
        )

    assert parent_data['ref_data'] == \
        reference_data[test_four_key]['ref_data']

def examine_metric_key_lookup(mtm, sample_data, model_data):

    reference_data = set(mtm.METRIC_KEYS)

    #assert number of model datums matches sample data
    assert len(model_data) == len(sample_data['results'])

    test_name = [sample_data['testrun']['suite']]

    reference_value_count = 0
    for p in sample_data['results']:
        reference_value_count += len( sample_data['results'][p] )

    model_value_count = 0
    for key in model_data:

        is_subset = reference_data.issubset(
            set(model_data[key]['ref_data'].keys())
            )

        #assert all metrics keys should be present in ref_data
        assert is_subset == True

        model_value_count += len(model_data[key]['values'])

    #assert total number of values in sample data matches
    #the data from the model
    assert reference_value_count == model_value_count

def setup_pushlog_walk_tests(
    mtm, ptm, plm, monkeypatch, load_objects=False
    ):
    """
    Builds the sample pushlog, iterates through each push storing
    a modified version of perftest_data where the testrun.date is
    set to the associated push date and test_build.revision is set to
    the push node.  In addition, two specialized sample data structures
    are created to test missing perftest data and abnormally high test
    values that should cause t-test failure.

    The setup_data structure returned can be used to test metric values,
    thresholds, summary data, and push log walking logic.
    """

    setup_data = {}
    now = int( time.time() )

    #monkey patch in sample pushlog
    def mock_urlopen(nuttin_honey):
        return get_pushlog_json_readable(get_pushlog_json_set())
    monkeypatch.setattr(urllib, 'urlopen', mock_urlopen)

    branch = 'Firefox'
    result = plm.store_pushlogs("test_host", 1, branch=branch)

    #load perftest data that corresponds to the pushlog data
    #store parent chain for tests
    setup_data['branch'] = branch
    setup_data['testsuite_name'] = ""
    setup_data['skip_revision'] = ""
    setup_data['skip_index'] = 2
    setup_data['fail_revision'] = ""
    setup_data['test_fail_index'] = 4
    setup_data['sample_revisions'] = []
    setup_data['sample_dates'] = {}

    setup_data['branch_pushlog'] = plm.get_branch_pushlog(1)

    #Build list of revisions to operate on
    for index, node in enumerate( setup_data['branch_pushlog'] ):
        revision = mtm.truncate_revision(node['node'])

        setup_data['sample_dates'][revision] = node['date']

        setup_data['sample_revisions'].append(revision)
        if index == setup_data['skip_index']:
            setup_data['skip_revision'] = revision
            continue

    #Load sample data for all of the revisions
    for index, revision in enumerate( setup_data['sample_revisions'] ):

        #if revision == setup_data['skip_revision']:
        if index == setup_data['skip_index']:
            continue

        sample_data = {}

        if index == setup_data['test_fail_index']:
            #Set up test run values to fail ttest
            data = [50000, 60000, 70000]

            sample_data = TestData( perftest_data(
                testrun={ 'date':setup_data['sample_dates'][revision] },
                test_build={ 'revision': revision, 'branch':branch },
                results={'one.com':data,
                         'two.com':data,
                         'three.com':data}
                )
            )
            setup_data['fail_revision'] = revision

        else:
            sample_data = TestData( perftest_data(
                testrun={ 'date':setup_data['sample_dates'][revision] },
                test_build={ 'revision': revision, 'branch':branch },
                )
            )

        if not setup_data['testsuite_name']:
            setup_data['testsuite_name'] = sample_data['testrun']['suite']

        if load_objects:
            ptm.store_test_data( json.dumps( sample_data ) )
            test_run_ids = ptm.process_objects(2)

            compute_test_run_metrics(
                ptm.project, plm.project, False, test_run_ids
            )

        else:
            #Load sample data
            ptm.load_test_data(sample_data)

    revision_count = len( setup_data['sample_revisions'] )

    setup_data['target_revision_index'] = revision_count - 1

    return setup_data

def _adapt_data(mtm, data):

    adapted_reference = {}
    for d in data:
        key = mtm.get_metrics_key(d)
        if key not in adapted_reference:
            #set reference data
            adapted_reference[key] = {
                'values':[],
                'ref_data':mtm.extend_with_metrics_keys(
                    d, ['test_run_id', 'test_name', 'revision']
                    )
                }

        adapted_reference[key]['values'].append( d['value'] )

    return adapted_reference

