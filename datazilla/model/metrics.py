import sys
import copy

from dzmetrics.ttest import welchs_ttest
from dzmetrics.fdr import rejector

class MetricsMethodFactory(object):
    """Class instance factory for different metric methods"""

    def __init__(self, metric_collection):

        self.metric_collection = metric_collection

        #Holds reusable metric method instances
        self.metric_method_instances = dict()

    def get_metric_method(self, test_name=None):
        """
        Returns the metric method instance associated with the test name
        provided.
        """
        metric_method = None

        #New metric method classes should be added to this
        #conditional with their appropriate test_name condition.  The
        #TtestMethod is the current default.
        if test_name == 'Talos tp5n':
            metric_method = self.metric_method_instances.setdefault(
                test_name, TtestMethod(self.metric_collection)
                )
        else:
            #Default metric method for all test suites
            metric_method = self.metric_method_instances.setdefault(
                test_name, TtestMethod(self.metric_collection)
                )

        return metric_method

class MetricMethodInterface(object):
    """Defines the interface for metric methods to use"""

    MSG = (
        "Derived classes of MetricMethodBase should"
        "implement this function"
        )

    def run_metric_method(self, child_data, parent_data):
        """
        Run the metric method.

        child_data = [ test_value1, test_value2, test_value3, ... ]
        parent_data = [ test_value1, test_value2, test_value3, ... ]
        """
        raise NotImplementedError(self.MSG)

    def run_metric_summary(self, data):
        """
        Run the metric summary method.

        data = [
            {
                value:test value,
                page_id:page_id,
                metric_value_id:metric_value_id,
                metric_value_name:metric_value_name
            } ...
        ]

        Derived classes that implement this method will need to filter
        data.values for cls.SUMMARY_NAME to retrive the data required.
        The base class method, filter_by_metric_value_name, can be
        used for this.
        """
        raise NotImplementedError(self.MSG)

    def evaluate_metric_result(self, test_result):
        """
        Should return True if the test passed, False if not.

        test_result - The return value from the run_metric method.
        """
        raise NotImplementedError(self.MSG)

    def evaluate_metric_summary_result(self, test_result):
        """
        Should return True if the summary test passed, False if not.

        test_result - The return value from the run_metric_summary method.
        """
        raise NotImplementedError(self.MSG)

    def get_data_for_metric_storage(
        self, ref_data, result, threshold_test_run_id
        ):
        """
        Get data for metric storage.

        ref_data = {
            all MetricsTestModel.METRIC_KEYS: associated id,
            test_run_id:id,
            test_name:"Talos test name",
            revision:revision
            }

        result = The return value from run_metric_method.

        threshold_test_run_id = test_run_id used as threshold/parent.
        """
        raise NotImplementedError(self.MSG)

    def get_data_for_summary_storage(
        self, ref_data, result, threshold_test_run_id
        ):
        """
        Get data for metric summary storage.

        ref_data = {
            all MetricsTestModel.METRIC_SUMMARY_KEYS: associated id,
            test_run_id:id,
            test_name:"Talos test name",
            revision:revision
            }

        result = The return value from run_metric_summary_method.

        threshold_test_run_id = test_run_id used as threshold/parent.
        """
        raise NotImplementedError(self.MSG)

class MetricMethodBase(MetricMethodInterface):
    """Base class for all metric methods"""

    def __init__(self, metric_collection):

        if not self.NAME:

            msg = (
                "Class, {0}, must set cls.NAME to a valid metric name "
                "found in the `metric` table in the "
                "perftest schema"
                ).format(self.__class__.__name__)

            raise MetricMethodError(msg)

        if not self.SUMMARY_NAME:

            msg = (
                "Class, {0}, must set cls.SUMMARY_NAME to a valid "
                "metric value name found in the `metric_value` table "
                "in the perftest schema or to None if there is no metric "
                "summary available."
                ).format(self.__class__.__name__)

            raise MetricMethodError(self.bad_summary_name_msg)

        ####
        # collection of all metric reference data
        ####
        self.metric_collection = metric_collection

        self.metric_id = None

        self.metric_values = {}

        self.set_metric_method()

    def set_metric_method(self):
        """
        Populates self.metric_id and self.metric_values for derived
        classes.  Requires derived classes set cls.NAME to a metric name
        found in the metric table in the perftest schema and
        cls.SUMMARY_NAME to a valid metric value name found in the
        `metric_value` table in the perftest schema or None if there is
        no metric summary for the method.
        """

        for data in self.metric_collection:
            if data['metric_name'] == self.NAME:

                if not self.metric_id:
                    self.metric_id = data['metric_id']

                self.metric_values[
                    data['metric_value_name']
                    ] = data['metric_value_id']

        if not self.metric_values:
            msg = ("self.metric_values not set for, self.NAME={0}, for "
                   "class, {1}").format(self.NAME, self.__class__.__name__)
            raise MetricMethodError(msg)

        if not self.metric_id:
            msg = ("self.metric_id not set for, self.NAME={0}, for "
                   "class, {1}").format(self.NAME, self.__class__.__name__)
            raise MetricMethodError(msg)

    def filter_by_metric_value_name(self, data):
        flist = filter(self._get_metric_value_name, data)
        return { 'values':map(lambda d: d['value'], flist), 'list':flist }

    def get_metric_id(self):
        return self.metric_id

    def _get_metric_value_name(self, datum):
        if datum['metric_value_name'] == self.metric_value_name:
            return True

class TtestMethod(MetricMethodBase):
    """Class implements the metric method interface for welch's ttest"""

    NAME = 'welch_ttest'
    SUMMARY_NAME = 'fdr'

    # Alpha value for ttests
    ALPHA = 0.05

    # Index to start collecting test values from
    DATA_START_INDEX = 1

    def __init__(self, metric_collection):

        super(TtestMethod, self).__init__(metric_collection)

        self.result_key = set([ 'p', 'h0_rejected', self.SUMMARY_NAME ])

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
            rd['metric_value_name'] = self.SUMMARY_NAME
            rd['metric_value_id'] = self.metric_values[self.SUMMARY_NAME]
            rd['value'] = s

            results.append(rd)

        return results

    def evaluate_metric_result(self, test_result):
        success = False
        ###
        # h0_rejected will be False from welchs_ttest() output but
        # it could also be 0 if retrieved directly from the database,
        ###
        if (test_result['h0_rejected'] == False) or \
            (test_result['h0_rejected'] == 0):
            success = True
        return success

    def evaluate_metric_summary_result(self, test_result):
        success = False
        ###
        # fdr will be False from rejector() output but
        # it could also be 0 if retrieved directly from the database,
        ###
        if (test_result[self.SUMMARY_NAME] == False) or \
            (test_result[self.SUMMARY_NAME] == 0):
            success = True
        return success

    def get_data_for_metric_storage(
        self, ref_data, result, threshold_test_run_id
        ):

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
                        value,
                        threshold_test_run_id
                    ]
                )

        return placeholders

    def get_data_for_summary_storage(
        self, ref_data, result, threshold_test_run_id
        ):

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
                        self.metric_values[ self.SUMMARY_NAME ],
                        ref_data['page_id'],
                        value,
                        threshold_test_run_id
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


class MetricMethodError:
    """
    Base class for all MetricMethod errors.  Takes an error message and
    returns string representation in __repr__.
    """
    def __init__(self, msg):
        self.msg = msg
    def __repr__(self):
        return self.msg

