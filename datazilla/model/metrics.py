from dzmetrics.ttest import welchs_ttest, fdr

class MetricsFactory(object):
    """Class instance factory for different metric methods"""

    def __init__(self, metrics):
        self.metrics = metrics

    def get_metric_method(self, test_suite=None):

        ###
        # Class instance factory
        #
        # New metric method classes should be added to this conditional
        # with their appropriate test_suite condition.  The TtestMethod
        # should be returned in the else clause.
        ###
        if not test_suite:
            #Default metric for all test suites
            return TtestMethod(self.metrics)

class MetricMethodInterface(object):
    """Defines the interface for metric methods to use"""

    MSG = 'Metric Method should implement this'

    def run_test(self):
        raise NotImplementedError(self.MSG)
    def evaluate_test_result(self):
        """Should return true if the test passed false if not"""
        raise NotImplementedError(self.MSG)
    def store_test(self):
        raise NotImplementedError(self.MSG)

class MetricMethodBase(MetricMethodInterface):
    """Base class for all metric methods"""

    def __init__(self, metric):

        self.metric = metric

    @classmethod
    def get_revision_from_node(cls, node):
        return node[0:12]

class TtestMethod(MetricMethodBase):
    """Class implements welch's ttest"""

    # Alpha value for ttests
    ALPHA = 0.05

    def __init__(self, metric):
        super(TtestMethod, self).__init__(metric)

        self.name = 'welch_ttest'

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

    def store_test(self, result):
        pass





