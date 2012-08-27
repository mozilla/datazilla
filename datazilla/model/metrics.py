import sys
import copy

from django.conf import settings

from dzmetrics.ttest import welchs_ttest
from dzmetrics.fdr import rejector

from base import DatazillaModelBase


class MetricsTestModel(DatazillaModelBase):
    """
    Public interface to all data access for the metrics part of the perftest
    schema.
    """

    # Content types that every project will have
    CONTENT_TYPES = ["perftest"]

    ###
    # Metric keys are used together to define a unique Metrics Datum
    #
    # Metrics Datum: A target for a metrics method made up of a single set
    # of test value replicates.
    #
    # Example: ttest applied to all the replicates associated with a given
    # test suite page.
    ###
    METRIC_KEYS = [
        'product_id',
        'operating_system_id',
        'processor',
        'test_id',
        'page_id'
        ]

    ###
    # Metric summary keys are used together to define a unique Metric
    # Summary Datum
    #
    # Metric Summary Datum: A target for a metrics method made up of
    # a single set of values computed by a metrics method.
    #
    # Example: fdr applied to all of the p values computed
    # in a ttest.
    ###
    METRIC_SUMMARY_KEYS = [
        'product_id',
        'operating_system_id',
        'processor',
        'test_id'
        ]

    KEY_DELIMITER = '__'

    #Number of characters in a node that are
    #used in the revision string
    REVISION_CHAR_COUNT = 12

    def __init__(self, project=None, metrics=()):
        super(MetricsTestModel, self).__init__(project)
        self.skip_revisions = set()

        self.metrics = metrics or self._get_metric_collection()

        self.mf = MetricsMethodFactory(self.metrics)

    @classmethod
    def get_metrics_key(cls, data):
        return cls.KEY_DELIMITER.join(
            map(lambda s: str( data[s] ), cls.METRIC_KEYS)
            )

    @classmethod
    def get_metrics_summary_key(cls, data):
        return cls.KEY_DELIMITER.join(
            map(lambda s: str( data[s] ), cls.METRIC_SUMMARY_KEYS)
            )

    @classmethod
    def extend_with_metrics_keys(cls, data, add_keys=[]):
        keys = []
        keys.extend(cls.METRIC_KEYS)
        if add_keys:
            keys.extend(add_keys)
        return dict([(k, data.get(k, None)) for k in keys])

    @classmethod
    def get_revision_from_node(cls, node):
        return node[0:cls.REVISION_CHAR_COUNT]

    def add_skip_revision(self, revision):
        if revision:
            self.skip_revisions.add(revision)

    def get_metric_summary_name(self, test_name):
        m = self.mf.get_metric_method(test_name)
        return m.SUMMARY_NAME

    def get_test_values(self, revision, struct_type='metric_key_lookup'):
        """
        Retrieve all test values associated with a given revision.

        revision - revision/changeset string.

        struct_type - Determines the structure of the data returned.
            Possible values are: metric_summary_lookup or metric_key_lookup.
            See adapt_data for detailed data structure descriptions.
        """

        proc = 'perftest.selects.get_test_values'

        revision_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[revision],
            return_type='tuple',
            )

        return self.adapt_data(struct_type, revision_data)

    def get_threshold_data(self, ref_data):
        """
        Retrieve all metric threshold data for a given metric key found
        in the supplied dictionary ref_data.

        ref_data - Dictionary containing all METRIC_KEYS and their
            associated values.
        """

        m = self.mf.get_metric_method(ref_data['test_name'])
        metric_id = m.get_metric_id()

        proc = 'perftest.selects.get_metric_threshold'

        placeholders = [
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['page_id']
            ]

        threshold_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            return_type='tuple',
            )

        return self.adapt_data('threshold_data_lookup', threshold_data)

    def get_metrics_data(self, revision):
        """
        Retrieve all metrics data associated with a given revision.
        """

        proc = 'perftest.selects.get_computed_metrics'

        computed_metrics = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[revision],
            return_type='tuple'
            )

        return self.adapt_data(
            'metric_data_lookup', computed_metrics
            )

    def get_parent_test_data(
        self, pushlog, index, child_key, metric_method_data=None
        ):
        """
        Walks back through the branch 'pushlog' starting at the 'index'
        position before the child, looking for the parent push of
        the metrics datum specified by 'child_key'.

        pushlog - Pushlog data structure for a given branch (generated by
            PushLogModel.get_branch_pushlog.

        index - Pushlog index where the child is found.

        child_key - Metrics datum key of the child to find a parent for.

        metric_method_data - Data for the metric method to use to validate
            metric test results.  If it's provided a parent must pass the
            MetricMethod.evaluate_metric_result test to be considered a
            viable parent.
        """

        parent_data = {}
        test_result = {}
        parent_index = index

        try:

            while not parent_data:

                if parent_index == 0:
                    break
                else:
                    #walk back through the pushlog to find the parent
                    parent_index -= 1

                parent_node = pushlog[ parent_index ]
                revision = self.get_revision_from_node(parent_node['node'])

                #skip pushes without data
                if revision in self.skip_revisions:
                    continue

                data = self.get_test_values(revision)

                #no data for this revision, skip
                if not data:
                    self.add_skip_revision(revision)
                    continue

                if child_key in data:
                    if metric_method_data:
                        m = self.mf.get_metric_method(
                            data[child_key]['ref_data']['test_name']
                            )

                        test_result = m.run_metric_method(
                            metric_method_data,
                            data[child_key]['values']
                            )

                        #Confirm that it passes test
                        if m.evaluate_metric_result(test_result):
                            #parent found that passes metric test
                            #requirements
                            parent_data = data[child_key]
                    else:
                        #parent found
                        parent_data = data[child_key]

        except IndexError:
            #last index reached, no parent with data found,
            #return empty data structures
            return parent_data, test_result

        else:
            #parent with data found
            return parent_data, test_result

    def run_metric_method(self, ref_data, child_data, parent_data):

        m = self.mf.get_metric_method(ref_data['test_name'])
        results = m.run_metric_method(child_data, parent_data)
        return results

    def run_metric_summary(self, ref_data, data):

        m = self.mf.get_metric_method(ref_data['test_name'])
        results = m.run_metric_summary(data)
        return results

    def store_metric_results(
        self, revision, ref_data, results,
        revision_pushlog_date, threshold_pushlog_date,
        threshold_test_run_id
        ):

        proc = 'perftest.inserts.set_test_page_metric'

        m = self.mf.get_metric_method(ref_data['test_name'])
        placeholders = m.get_data_for_metric_storage(
            ref_data, results, threshold_test_run_id
            )

        if placeholders:

            self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )

            if m.evaluate_metric_result(results):
                if threshold_pushlog_date:
                    #####
                    # Don't update the threshold metric if the pushlog date
                    # associated with this revision is from the past.
                    ####
                    if int(revision_pushlog_date) >= \
                        int(threshold_pushlog_date):

                        self.insert_or_update_metric_threshold(
                            revision,
                            ref_data,
                            m.get_metric_id(),
                            revision_pushlog_date
                            )
                else:
                    ####
                    # If no threshold pushlog date is provided this is an
                    # insert, the data was derived from a direct comparison
                    # with a pushlog parent.
                    ####
                    self.insert_or_update_metric_threshold(
                        revision,
                        ref_data,
                        m.get_metric_id(),
                        revision_pushlog_date
                        )

    def store_metric_summary_results(
        self, revision, ref_data, results, threshold_test_run_id
        ):

        proc = 'perftest.inserts.set_test_page_metric'

        m = self.mf.get_metric_method(ref_data['test_name'])

        placeholders = m.get_data_for_summary_storage(
            ref_data, results, threshold_test_run_id
            )

        if placeholders:

            self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )

    def insert_or_update_metric_threshold(
        self, revision, ref_data, metric_id, push_date
        ):

        proc = 'perftest.inserts.set_metric_threshold'

        placeholders = [

            ##Insert Placeholders
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['test_run_id'],
            revision,
            push_date,

            ##Duplicate Key Placeholders
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['test_run_id'],
            revision,
            push_date
            ]

        self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=settings.DEBUG,
            placeholders=placeholders
            )

    def adapt_data(self, struct_type, data):

        adapted_data = {}

        if struct_type == 'metric_summary_lookup':
            adapted_data = self._get_metric_summary_key_lookup(data)
        elif struct_type == 'metric_key_lookup':
            adapted_data = self._get_metric_key_lookup(data)
        elif struct_type == 'threshold_data_lookup':
            adapted_data = self._get_threshold_data_lookup(data)
        elif struct_type == 'metric_data_lookup':
            adapted_data = self._get_metric_data_lookup(data)
        else:
            adapted_data = self._get_metric_key_lookup(data)

        return adapted_data

    def _get_metric_data_lookup(self, data):
        """
        Converts datasource tuple to

        metric_key : {
            { ref_data: {
                all self.METRIC_KEYS: associated id,
                test_run_id:id,
                threshold_test_run_id:test_run_id of threshold used,
                test_name:"Talos test name",
                revision:revision
                }
            },

           { values : [ {
                value:test value,
                page_id:page_id,
                metric_value_id:metric_value_id,
                metric_value_name:metric_value_name
                }, ...
             ]
           }
        }
        """

        key_lookup = {}
        for d in data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id',
                            'test_name',
                            'revision',
                            'threshold_test_run_id']
                        )
                    }
            key_lookup[key]['values'].append( {
                'value':d['value'],
                'page_id':d['page_id'],
                'metric_value_id':d['metric_value_id'],
                'metric_value_name':d['metric_value_name']
                } )

        return key_lookup

    def _get_threshold_data_lookup(self, data):
        """
        Converts datasource tuple to

        metric_key : {
            { ref_data: {
                all self.METRIC_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision,
                push_date: int representing time associated with the push
                           this datum came from.
                }
            },

           { values : [ test_value1, test_value2, test_value3, ... ] }
        }
        """

        key_lookup = {}
        for d in data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name',
                            'revision', 'push_date']
                        )
                    }

            key_lookup[key]['values'].append( d['value'] )

        return key_lookup

    def _get_metric_key_lookup(self, data):
        """
        Converts datasource tuple to

        metric_key : {
            { ref_data: {
                all self.METRIC_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision
                }
            },

           { values : [ test_value1, test_value2, test_value3, ... ] }
        }
        """

        key_lookup = {}
        for d in data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision']
                        )
                    }
            key_lookup[key]['values'].append( d['value'] )

        return key_lookup

    def _get_metric_summary_key_lookup(self, data):
        """
        Converts datasource tuple to

        metric_summary_key : {
            { ref_data: {
                all self.METRIC_SUMMARY_KEYS: associated id,
                test_run_id:id,
                test_name:"Talos test name",
                revision:revision
                }
            },

           { values : [ {
                dict containing all key/value pairs from the
                SELECT
                }, ...
             ]
           }
        }
        """

        test_lookup = {}
        for d in data:
            key = self.get_metrics_summary_key(data)
            if key not in test_lookup:
                #set reference data
                test_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision']
                        )
                    }
            test_lookup[key]['values'].append(d)

        return test_lookup

    def _get_metric_collection(self):
        proc = 'perftest.selects.get_metric_collection'

        metric_collection = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='metric_name',
            return_type='tuple',
            )
        return metric_collection

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
        Run the metric method and return results.

        child_data = [ test_value1, test_value2, test_value3, ... ]
        parent_data = [ test_value1, test_value2, test_value3, ... ]
        """
        raise NotImplementedError(self.MSG)

    def run_metric_summary(self, data):
        """
        Run the metric summary method and return results.

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
        Get data for metric storage.  Should return a list of
        placeholders for perftest.inserts.set_test_page_metric

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
        Get data for metric summary storage.  Should return a list of
        placeholders for perftest.inserts.set_test_page_metric

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

