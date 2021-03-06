import json
import os

from datazilla.model.base import TestData

from ..sample_data import perftest_data
from ..sample_metric_data import get_metric_collection_data

from datazilla.model import (
    MetricsMethodFactory, MetricMethodBase, TtestMethod, MetricMethodError
    )

def test_metrics_factory():

    sample_data = TestData(perftest_data())

    metric_collection_data = get_metric_collection_data()

    mmf = MetricsMethodFactory(
        metric_collection_data['initialization_data']
        )

    m_one = mmf.get_metric_method(metric_collection_data['testsuite_name'])

    #Should have one cached metric method instance
    assert len(mmf.metric_method_instances) == 1

    #Retrieve metric method again, should still have one cached metric
    #method instance
    m_two = mmf.get_metric_method(metric_collection_data['testsuite_name'])

    assert len(mmf.metric_method_instances) == 1

    #get_metric_method should return a TtestMethod class instance for
    #the sample data
    tm = TtestMethod(metric_collection_data['initialization_data'])
    assert m_one.__class__.__name__ == tm.__class__.__name__
    assert m_two.__class__.__name__ == tm.__class__.__name__

def test_ttest_nan():

    metric_collection_data = get_metric_collection_data()

    tm = TtestMethod(metric_collection_data['initialization_data'])

    #####
    #These child/parent values will generate a stddev of 0
    #which will create a nan and throw an error
    #####
    try:
        tm.run_metric_method([6,6,6,6], [6,6,6,6])
    except MetricMethodError as e:
        assert "p value is not a number" in unicode(e)
    else:
        raise Exception('Failed to raise MetricMethodError')

