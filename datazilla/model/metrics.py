import sys

from dzmetrics.ttest import welchs_ttest, fdr

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
        # should be returned in the else clause.
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

    def run_test(self):
        raise NotImplementedError(self.MSG)
    def evaluate_test_result(self):
        """Should return true if the test passed false if not"""
        raise NotImplementedError(self.MSG)
    def get_data_for_storage(self):
        raise NotImplementedError(self.MSG)

class MetricMethodBase(MetricMethodInterface):
    """Base class for all metric methods"""

    def __init__(self, metric):

        self.metric = metric

        self.metric_id = None
        self.metric_values = {}

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


class TtestMethod(MetricMethodBase):
    """Class implements welch's ttest"""

    # Alpha value for ttests
    ALPHA = 0.05

    def __init__(self, metric):
        super(TtestMethod, self).__init__(metric)

        self.name = 'welch_ttest'

        self.result_key = set(['p', 'h0_rejected'])

        self.set_metric_method()

    def run_test(self, child_data, parent_data):

        result = welchs_ttest(
            child_data,
            parent_data,
            self.ALPHA
            )

        return result

    def evaluate_test_result(self, test_result):
        success = False
        if not test_result['h0_rejected']:
            success = True
        return success

    def get_data_for_storage(self, ref_data, result):

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

    def get_metric_value(self, metric_value_name, result):

        value = None
        if metric_value_name in self.result_key:
            value = result[metric_value_name]
        else:
            value = result[metric_value_name + str(1)]

        return value



