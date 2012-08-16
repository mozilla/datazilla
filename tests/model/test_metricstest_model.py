import json
import datetime
import copy
import urllib

from datazilla.model.base import TestData

from ..sample_data import perftest_data
from ..sample_pushlog import pushlog_json
from ..sample_metric_data import *

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

    data = get_metrics_key_data(
        key_delimiter=mtm.KEY_DELIMITER
        )

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
    assert test_data['test_run_id'] == model_data['test_run_id']
    assert test_data['test_name'] == model_data['test_name']

def test_get_revision_from_node(mtm):

    reference_data = 'asdf781435quhafo8qy3lrhaos8eyajkwwehfqywralisudyf9a'

    revision = mtm.get_revision_from_node(reference_data)

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
    model_data = mtm.get_test_values(revision, 'metric_key_lookup')

    _test_metric_key_lookup(mtm, sample_data, model_data)

def test_get_test_values(mtm, ptm):

    sample_data = TestData(perftest_data())

    sample_revision = sample_data['test_build']['revision']

    ptm.load_test_data(sample_data)

    model_data = mtm.get_test_values(sample_revision, 'metric_key_lookup')

    _test_metric_key_lookup(mtm, sample_data, model_data)

def test_get_threshold_data(ptm, mtm):

    child_sample_data = TestData( perftest_data() )
    child_revision = child_sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'

    parent_sample_data = TestData( perftest_data(
        test_build={ 'revision': parent_revision }
        )
    )

    ref_data = get_sample_ref_data()

    #We need to load some data so the foreign
    #key constraints for the reference data are
    #valid
    ptm.load_test_data(child_sample_data)
    ptm.load_test_data(parent_sample_data)

    sample_ttest_data = get_sample_ttest_data()

    #The sample data ttest passes with itself this
    #causes the data to be stored as threshold data
    mtm.store_metric_results(
        child_revision, ref_data, sample_ttest_data
        )

    metric_id = 1
    placeholders = [
        ref_data['product_id'],
        ref_data['operating_system_id'],
        ref_data['processor'],
        metric_id,
        ref_data['test_id'],
        ref_data['page_id'],
        ref_data['page_id']
        ]

    metric_data_reference = ptm.sources["perftest"].dhub.execute(
        proc="perftest.selects.get_metric_threshold",
        placeholders=placeholders)

    adapted_reference = mtm.adapt_data(
        'metric_key_lookup',
        metric_data_reference
        )

    threshold_data = mtm.get_threshold_data(ref_data, 'metric_key_lookup')

    assert threshold_data == adapted_reference

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

    #Get sample data
    child_sample_data = TestData(perftest_data())
    test_name = child_sample_data['testrun']['suite']
    child_revision = child_sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'

    parent_sample_data = TestData( perftest_data(
        test_build={ 'revision': parent_revision }
        )
    )

    #Need to store data to satisfy foreign key requirements
    ptm.load_test_data(child_sample_data)
    ptm.load_test_data(parent_sample_data)

    child_data = mtm.get_test_values(child_revision, 'metric_key_lookup')
    parent_data = mtm.get_test_values(parent_revision, 'metric_key_lookup')

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
            results
            )

        #Retrieve the metric data
        metrics_data = mtm.get_metrics_data(child_revision)

        #Compute the metric summary
        summary_results = mtm.run_metric_summary(
            metrics_data[key]['ref_data'], metrics_data[key]['values']
            )

        #Store the metric summary results
        mtm.store_metric_summary_results(
            child_revision,
            metrics_data[key]['ref_data'],
            summary_results
            )

        #Metric data should contain the summary results
        summary_metrics_data = mtm.get_metrics_data(child_revision)

        for data in summary_metrics_data[key]['values']:
            if data['metric_value_name'] == summary_name:
                #We should find the computed summary data in in
                #the data retrieved
                assert summary_results[0]['page_id'] == data['page_id']
                assert summary_results[0]['value'] == data['value']


def test_store_metric_results(mtm, ptm):

    child_sample_data = TestData( perftest_data() )
    child_revision = child_sample_data['test_build']['revision']

    parent_revision = 'a461b5f53b20'

    parent_sample_data = TestData( perftest_data(
        test_build={ 'revision': parent_revision }
        )
    )

    ref_data = get_sample_ref_data()

    #We need to load some data so the foreign
    #key constraints for the reference data are
    #valid
    ptm.load_test_data(child_sample_data)
    ptm.load_test_data(parent_sample_data)

    sample_ttest_data = get_sample_ttest_data()

    mtm.store_metric_results(
        child_revision, ref_data, sample_ttest_data
        )

    metric_data_reference = ptm.sources["perftest"].dhub.execute(
        proc="perftest.selects.get_computed_metrics",
        placeholders=[child_revision])

    adapted_reference = mtm.adapt_data(
        'metric_data_lookup',
        metric_data_reference
        )

    child_data = mtm.get_metrics_data(child_revision)

    reference_keys = adapted_reference.keys()
    data_keys = child_data.keys()

    assert data_keys == reference_keys

    for key in reference_keys:

        assert child_data[key]['values'] == adapted_reference[key]['values']


def test_insert_or_update_metric_threshold(mtm, ptm):

    # get sample data
    sample_data = TestData( perftest_data(
        results={'one.com':[10,20,30,40]}
        )
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
    ptm.load_test_data(sample_data)
    ptm.load_test_data(parent_sample_data)

    # retrieve loaded test values
    model_data = mtm.get_test_values(revision, 'metric_key_lookup')
    parent_model_data = mtm.get_test_values(
        parent_revision, 'metric_key_lookup'
        )

    # retrieve metric id for insert_or_update_threshold
    metric_method = mtm.mf.get_metric_method(test_name)
    metric_id = metric_method.get_metric_id()

    for key in model_data:

        #First pass should be inserting not updating
        mtm.insert_or_update_metric_threshold(
            revision, model_data[key]['ref_data'], metric_id
            )

        inserted_threshold_data = mtm.get_threshold_data(
            model_data[key]['ref_data']
            )

        #We should get the model_data back here
        assert model_data[key]['ref_data'] == inserted_threshold_data[key]['ref_data']
        assert model_data[key]['values'] == inserted_threshold_data[key]['values']

    for key in parent_model_data:

        #Second pass should be updating updating not inserting
        mtm.insert_or_update_metric_threshold(
            parent_revision, parent_model_data[key]['ref_data'], metric_id
            )
        #use child ref data to retrieve thresholds
        updated_threshold_data = mtm.get_threshold_data(
            model_data[key]['ref_data']
            )

        #thresholds should point to the parent now
        assert parent_model_data[key]['ref_data'] == updated_threshold_data[key]['ref_data']
        assert parent_model_data[key]['values'] == updated_threshold_data[key]['values']

        #parent model data will have a test_run_id of 2 since it's the
        #second one inserted, this should now be the test_run_id associated
        #with the threshold data
        assert 2 == updated_threshold_data[key]['ref_data']['test_run_id']

def _test_metric_key_lookup(mtm, sample_data, model_data):

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

def _test_metric_summary_lookup():

    pass



