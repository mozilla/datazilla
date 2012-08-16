import sys
import copy

from dzmetrics.ttest import welchs_ttest
from dzmetrics.fdr import rejector

class MetricsFactory(object):
    """Class instance factory for different metric methods"""

    def __init__(self, metrics):
        self.metrics = metrics

    def get_metric_method(self, test_name=None):

        ###
        # Class instance factory
        #
        # New metric method classes should be added to this conditional
        # with their appropriate test_suite condition.  The TtestMethod
        # is the current default.
        ###
        metric_method = None
        if test_name == 'Talos tp5n':
            metric_method = TtestMethod(self.metrics)
        else:
            #Default metric for all test suites
            metric_method = TtestMethod(self.metrics)

        return metric_method

class MetricMethodInterface(object):
    """Defines the interface for metric methods to use"""

    MSG = 'Metric methods should implement this function'

    def run_metric_method(self):
        raise NotImplementedError(self.MSG)
    def run_metric_summary(self):
        raise NotImplementedError(self.MSG)
    def evaluate_metric_result(self):
        """Should return true if the test passed false if not"""
        raise NotImplementedError(self.MSG)
    def get_data_for_metric_storage(self):
        raise NotImplementedError(self.MSG)
    def get_data_for_summary_storage(self):
        raise NotImplementedError(self.MSG)

class MetricMethodBase(MetricMethodInterface):
    """Base class for all metric methods"""

    def __init__(self, metric):

        self.metric = metric

        self.metric_id = None

        self.metric_values = {}

        self.set_metric_method()

    @classmethod
    def get_revision_from_node(cls, node):
        return node[0:12]

    def set_metric_method(self):
        for data in self.metric:
            if data['metric_name'] == self.name:

                if not self.metric_id:
                    self.metric_id = data['metric_id']

                self.metric_values[
                    data['metric_value_name']
                    ] = data['metric_value_id']

        ##Need to throw some sort of error here indicating
        ##the metric name was not found

    def filter_by_metric_value_name(self, data):
        flist = filter(self._get_metric_value_name, data)
        return { 'values':map(lambda d: d['value'], flist), 'list':flist }

    def get_summary_name(self):
        return self.summary

    def get_metric_id(self):
        return self.metric_id

    def _get_metric_value_name(self, datum):
        if datum['metric_value_name'] == self.metric_value_name:
            return True

class TtestMethod(MetricMethodBase):
    """Class implements welch's ttest"""

    # Alpha value for ttests
    ALPHA = 0.05

    DATA_START_INDEX = 1

    def __init__(self, metric):

        self.name = 'welch_ttest'

        super(TtestMethod, self).__init__(metric)

        self.summary = 'fdr'

        self.result_key = set(['p', 'h0_rejected', self.summary])


        #Store p value id for fdr
        self.metric_value_name = 'p'

    def run_metric_method(self, child_data, parent_data):

        #Filter out the first replicate here
        result = welchs_ttest(
            child_data[self.DATA_START_INDEX:],
            parent_data[self.DATA_START_INDEX:],
            self.ALPHA
            )

        return result

    def run_metric_summary(self, data):

        filtered_data = self.filter_by_metric_value_name(data)
        rejector_data = rejector(filtered_data['values'])

        results = []
        for s, d in zip( rejector_data['status'], filtered_data['list'] ):

            rd = copy.copy(d)
            rd['metric_value_name'] = self.summary
            rd['metric_value_id'] = self.metric_values[ self.summary ]
            rd['value'] = s

            results.append(rd)

        return results

    def evaluate_metric_result(self, test_result):
        success = False
        if not test_result['h0_rejected']:
            success = True
        return success

    def get_data_for_metric_storage(self, ref_data, result):

        test_run_id = ref_data['test_run_id']

        placeholders = []

        for metric_value_name in self.metric_values:
            value = self.get_metric_value(metric_value_name, result)

            if metric_value_name == 'h0_rejected':

                if value == False:
                    value = 0
                else:
                    value = 1

            if value != None:

                placeholders.append(
                    [
                        test_run_id,
                        self.metric_id,
                        self.metric_values[ metric_value_name ],
                        ref_data['page_id'],
                        value
                    ]
                )

        return placeholders

    def get_data_for_summary_storage(self, ref_data, result):

        test_run_id = ref_data['test_run_id']

        placeholders = []

        for d in result:
            value = d['value']

            if value == False:
                value = 0
            else:
                value = 1

            if value != None:
                placeholders.append(
                    [
                        test_run_id,
                        self.metric_id,
                        self.metric_values[ self.summary ],
                        ref_data['page_id'],
                        value
                    ]
                )

        return placeholders

    def get_metric_value(self, metric_value_name, result):

        value = None

        try:

            if metric_value_name in self.result_key:
                value = result[metric_value_name]
            else:
                value = result[metric_value_name + str(1)]

        except KeyError:
            #metric_value_name not in result, return None
            return value
        else:
            return value


