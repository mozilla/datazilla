"""
Functions for flexible generation of sample input perftest JSON.

"""
import json
import os

from datazilla.model.metrics import TtestMethod

from dzmetrics.ttest import welchs_ttest
from dzmetrics.fdr import rejector

def get_metrics_key_data(**kwargs):

    defaults = {
        "product_id": kwargs.pop("product_id", 1),
        "operating_system_id": kwargs.pop("operating_system_id", 1),
        "processor": kwargs.pop("processor", 'x86_64'),
        "build_type": kwargs.pop("build_type", 'opt'),
        "test_id": kwargs.pop("test_id", 1),
        "page_id": kwargs.pop("page_id", 1),
        }

    defaults.update(kwargs)

    default_value = '1{0}1{0}x86_64{0}opt{0}1{0}1'.format(
        kwargs.pop('key_delimiter', '__')
        )

    return { 'key_data':defaults, 'default_value':default_value }

def get_metrics_summary_key_data(**kwargs):

    defaults = {
        "product_id": kwargs.pop("product_id", 1),
        "operating_system_id": kwargs.pop("operating_system_id", 1),
        "processor": kwargs.pop("processor", 'x86_64'),
        "build_type": kwargs.pop("build_type", 'opt'),
        "test_id": kwargs.pop("test_id", 1),
        }

    defaults.update(kwargs)

    default_value = '1{0}1{0}x86_64{0}opt{0}1'.format(
        kwargs.pop('key_delimiter', '__')
        )

    return { 'key_data':defaults, 'default_value':default_value }

def get_metric_values():

    return set(['stddev', 'mean', 'p', 'h0_rejected', 'n_replicates',
                'fdr', 'trend_stddev', 'trend_mean', 'pushlog_id',
                'push_date', 'test_evaluation'])

def get_metric_collection_data():

    defaults = (
        {'metric_value_name': 'std',
         'metric_value_id': 1,
         'metric_id': 1,
         'metric_name': 'welch_ttest'},

        {'metric_value_name': 'mean',
         'metric_value_id': 2,
         'metric_id': 1,
         'metric_name': 'welch_ttest'},

         {'metric_value_name': 'p',
          'metric_value_id': 3,
          'metric_id': 1,
          'metric_name':'welch_ttest'},

         {'metric_value_name': 'h0_rejected',
          'metric_value_id': 4,
          'metric_id': 1,
          'metric_name': 'welch_ttest'},

         {'metric_value_name': 'fdr',
          'metric_value_id': 5,
          'metric_id': 1,
          'metric_name': 'welch_ttest'},

         {'metric_value_name': 'pushlog_id',
          'metric_value_id': 6,
          'metric_id': 1,
          'metric_name': 'welch_ttest'},

         {'metric_value_name': 'push_date',
          'metric_value_id': 7,
          'metric_id': 1,
          'metric_name': 'welch_ttest'},

         {'metric_value_name': 'trend_mean',
          'metric_value_id': 8,
          'metric_id': 1,
          'metric_name': 'welch_ttest'},

         {'metric_value_name': 'trend_stddev',
          'metric_value_id': 8,
          'metric_id': 1,
          'metric_name': 'welch_ttest'},
          )

    metric_collection_data = {
        'initialization_data':defaults,
        'metric_summary_name':'fdr',
        'testsuite_name':'Talos tp5n'
        }

    return metric_collection_data

def get_sample_p_values():

    p_values = [0.5, 0.01, 0.01, 0.01, 0.2, 0.1, 0.1, 0.1, 0.001, 0.001]

    db_struct = []
    for v in p_values:
        db_struct.append(
            {'metric_value_name':'p',
             'value':v,
             'page_id':1
             }
        )

    return {'p_values':p_values, 'db_struct':db_struct}

def get_metric_sample_data_summary():

    p_values = get_sample_p_values()['p_values']
    results = rejector( p_values )
    return results

def get_metric_sample_data(key, sample_data):

    alpha = TtestMethod.ALPHA

    values = sample_data['results'][key][1:]
    results = welchs_ttest( values, values, alpha )

    return results

def get_sample_ref_data():
    return { 'test_name':'Talos tp5r',
             'test_run_id':1,
             'product_id':1,
             'operating_system_id':1,
             'processor':'x86_64',
             'build_type':'opt',
             'test_id':1,
             'page_id':1}

def get_sample_ttest_data():

    ttest_sample_data = {
        'stddev2': 24.041630,
        'mean2': 722.0,
        'p': 0.5,
        'h0_rejected': False,
        'stddev1': 24.041630,
        'mean1': 722.0
        }

    return ttest_sample_data
