import sys
import copy
import time

from numpy import mean, std, isnan, nan

from django.conf import settings

from dzmetrics.ttest import welchs_ttest, welchs_ttest_internal
from dzmetrics.fdr import rejector
from dzmetrics.data_smoothing import exp_smooth

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
        'build_type',
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
        'build_type',
        'test_id'
        ]

    KEY_DELIMITER = '__'

    #Number of characters in a node that are
    #used in the revision string
    REVISION_CHAR_COUNT = 12

    ALL_DIMENSION_COLUMN_KEY = {
        "ti":"test_run_id",
        "dr":"date received",
        "r":"revision",
        "p":"product",
        "b":"branch",
        "bv":"branch version",
        "osn":"operating system",
        "osv":"operating system version",
        "pr":"processor",
        "bt":"build type",
        "mn":"machine name",
        "pi":"pushlog_id",
        "pd":"push date",
        "tn":"test name",
        "pu":"page url",
        "m":"mean",
        "s":"std",
        "hr":"h0 rejected",
        "pv":"p value",
        "nr":"replicates",
        "f":"false discovery rate",
        "tm":"trend mean",
        "ts":"trend std",
        "te":"test evaluation"
        }

    def __init__(self, project=None, metrics=()):
        super(MetricsTestModel, self).__init__(project)
        self.skip_revisions = set()

        self.metrics = metrics or self._get_metric_collection()

        self.mf = MetricsMethodFactory(self.metrics)

        self.push_value_names = set(['push_date', 'pushlog_id'])

        self.format_float_values = set(
            ['mean', 'stddev', 'trend_mean', 'trend_stddev']
            )
        self.format_boolean_values = set(
            ['fdr', 'h0_rejected', 'test_evaluation']
            )

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
    def truncate_revision(cls, full_revision):
        return full_revision[0:cls.REVISION_CHAR_COUNT]

    def add_skip_revision(self, revision):
        if revision:
            self.skip_revisions.add(revision)

    def get_metric_summary_name(self, test_name):
        m = self.mf.get_metric_method(test_name)
        return m.SUMMARY_NAME

    def get_test_runs_not_in_all_dimensions(self, time_constraint):

        proc = 'perftest.selects.get_test_run_ids_not_in_all_dimensions'

        test_run_ids = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            key_column='id',
            placeholders=[time_constraint, time_constraint],
            return_type='set',
            )

        return list(test_run_ids)

    def get_test_values_by_test_run_id(self, test_run_id):
        """
        Retrieve all test values associated with a given test_run_id.

        test_run_id - test run id

        returns the following dictionary:

            metric_key : {
                    ref_data: {
                        all self.METRIC_KEYS: associated id,
                        test_run_id:id,
                        test_name:"Talos test name",
                        revision:revision
                    },

                    values : [ test_value1, test_value2, test_value3, ... ]
           }
        """
        proc = 'perftest.selects.get_test_values_by_test_run_id'

        revision_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[test_run_id],
            return_type='tuple',
            )

        return self._adapt_test_values(revision_data)

    def get_test_values_by_revision(self, revision, ref_data={}):
        """
        Retrieve all test values associated with a given revision.

        revision - revision/changeset string.

        ref_data - optional dictionary containing:

                    ref_data: {
                        all self.METRIC_KEYS: associated id,
                        test_name:"Talos test name",
                        revision:revision
                    },

                    If provided only data associated with the specific
                    metric key will be retrieved.

        returns the following dictionary:

            metric_key : {
                    ref_data: {
                        all self.METRIC_KEYS: associated id,
                        test_run_id:id,
                        test_name:"Talos test name",
                        revision:revision
                    },

                    values : [ test_value1, test_value2, test_value3, ... ]
           }
        """
        proc = 'perftest.selects.get_test_values_by_revision'

        placeholders = []

        if ref_data:

            proc = 'perftest.selects.get_test_values_by_ref_data'

            placeholders.append(ref_data['product_id'])
            placeholders.append(ref_data['operating_system_id'])
            placeholders.append(ref_data['processor'])
            placeholders.append(ref_data['build_type'])
            placeholders.append(ref_data['test_id'])

        placeholders.append(revision)

        revision_data = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            return_type='tuple',
            )

        return self._adapt_test_values(revision_data)

    def _adapt_test_values(self, revision_data):

        key_lookup = {}
        for d in revision_data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision', 'branch']
                        )
                    }
            key_lookup[key]['values'].append( d['value'] )

        return key_lookup

    def get_threshold_data(self, ref_data):
        """
        Retrieve all metric threshold data for a given metric key found
        in the supplied dictionary ref_data.

        ref_data - Dictionary containing all METRIC_KEYS and their
            associated values.

        returns the following dictionary:

            metric_key : {
                ref_data: {
                    all self.METRIC_KEYS: associated id,
                    test_run_id:id,
                    test_name:"Talos test name",
                    revision:revision
                },

                values : [ test_value1, test_value2, test_value3, ... ]

                metric_values:{ metric_value_name: metric_value, ... }
            }
        """
        m = self.mf.get_metric_method(ref_data['test_name'])
        metric_id = m.get_metric_id()

        #Get the threshold test run id
        test_run_proc = 'perftest.selects.get_metric_threshold_test_run'

        test_run_placeholders = [
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            ref_data['build_type'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id']
            ]

        test_run_data = self.sources["perftest"].dhub.execute(
            proc=test_run_proc,
            debug_show=self.DEBUG,
            placeholders=test_run_placeholders,
            return_type='iter',
            )

        test_run_id =  test_run_data.get_column_data('test_run_id')

        #Get the test values for the test run and page
        test_data_proc = \
            'perftest.selects.get_test_values_by_test_run_id_and_page_id'

        test_data = self.sources["perftest"].dhub.execute(
            proc=test_data_proc,
            debug_show=self.DEBUG,
            placeholders=[ test_run_id, ref_data['page_id'] ],
            return_type='tuple',
            )

        #Get the metric values for the test run and page
        metric_data_proc = \
            'perftest.selects.get_metrics_data_from_test_run_id_and_page_id'

        metrics_data = self.sources["perftest"].dhub.execute(
            proc=metric_data_proc,
            debug_show=self.DEBUG,
            placeholders=[ test_run_id, ref_data['page_id'] ],
            return_type='tuple',
            )

        key_lookup = {}

        #Load metrics data
        for d in metrics_data:
            key = self.get_metrics_key(d)
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'metric_values':{},
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision',
                            'metric_id', 'threshold_test_run_id']
                        )
                    }

            key_lookup[key]['metric_values'].setdefault(
                d['metric_value_name'], d['metric_value']
                )

        #Load associated test data
        for d in test_data:
            key = self.get_metrics_key(d)
            #The key should be defined at this point but if
            #not be sure to return any values
            if key not in key_lookup:
                #set reference data
                key_lookup[key] = {
                    'values':[],
                    'metric_values':{},
                    'ref_data':self.extend_with_metrics_keys(
                        d, ['test_run_id', 'test_name', 'revision',
                        'threshold_test_run_id']
                        )
                    }

            key_lookup[key]['values'].append( d['value'] )

        return key_lookup

    def get_metrics_data_from_ref_data(self, ref_data, test_run_id):

        proc = 'perftest.selects.get_metrics_data_from_ref_data'

        computed_metrics = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[
                ref_data['product_id'],
                ref_data['operating_system_id'],
                ref_data['processor'],
                ref_data['build_type'],
                ref_data['test_id'],
                test_run_id
                ],
            return_type='tuple'
            )

        key_lookup = {}
        for d in computed_metrics:
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

            key_lookup[key]['values'].append({
                'value':d['value'],
                'page_id':d['page_id'],
                'metric_value_id':d['metric_value_id'],
                'metric_value_name':d['metric_value_name']
                })

        return key_lookup

    def get_threshold_revision_lookup(self, threshold_test_run_ids):

        revision_lookup = {}
        if threshold_test_run_ids:
            threshold_proc = 'perftest.selects.get_threshold_revisions'

            r_string = ','.join( map( lambda tr_id: '%s', threshold_test_run_ids ) )

            revision_data = self.sources["perftest"].dhub.execute(
                proc=threshold_proc,
                debug_show=self.DEBUG,
                placeholders=list(threshold_test_run_ids),
                replace=[r_string]
                )

            for d in revision_data:
                revision_lookup[ d['id'] ] = d['revision']

        return revision_lookup

    def get_metrics_data_from_test_run_ids(self, test_run_ids, page_name):
        """
        Retrieve all metrics data associated with a given revision.

        returns the following list of dictionaries:

        [
            {
                test_machine: {
                    "platform": "x86_64",
                    "osversion": "fedora 12",
                    "os": "linux",
                    "name": "talos-r3-fed64-011"
                },
                testrun: {
                    "date": "1342730435",
                    "suite": "Talos tsspider.2",
                    "test_run_id":"1827313"
                },
                test_build: {
                    "id": "20120719120951",
                    "version": "15.0",
                    "name": "Firefox",
                    "branch": "Mozilla-Beta",
                    "revision": "ebfad1bf8749"
                },
                push_info: {
                    "push_date":123412341234,
                    "pushlog_id":12341234
                },
                pages: {
                    "layers1.html": {
                        stddev: value,
                        mean: value
                        p: value,
                        h0_rejected: value,
                        n_replicates: value,
                        fdr: value,
                        trend_stddev: value,
                        trend_mean: value,
                        push_date: value,
                        test_evaluation: value,
                    },

                    ...
                },

                ...
        [
        """
        if not test_run_ids:
            return []

        r_string = ','.join( map( lambda tr_id: '%s', test_run_ids ) )

        proc = 'perftest.selects.get_computed_metrics_from_test_run_ids'

        computed_metrics = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            replace=[r_string],
            placeholders=test_run_ids,
            return_type='tuple'
            )

        key_lookup = {}

        #Build a page lookup to filter by
        page_names = set()
        if page_name:
            map(
                lambda page:page_names.add(page.strip()),
                page_name.split(',')
                )

        threshold_test_run_ids = set()

        for d in computed_metrics:
            ####
            #Add revision to summary key to handle getting a mix of test
            #run ids from different revisions
            ####
            summary_key = "{0}{1}{2}".format(
                self.get_metrics_summary_key(d),
                self.KEY_DELIMITER,
                d['revision']
                )

            if page_names and (d['page_name'] not in page_names):
                continue

            if summary_key not in key_lookup:
                #set reference data

                key_lookup[summary_key] = {
                    'test_machine':{
                        "platform": d['processor'],
                        "osversion": d['operating_system_version'],
                        "os": d['operating_system_name'],
                        "name": d['machine_name']
                    },
                    'testrun':{
                        "date": d['date'],
                        "suite": d['test_name'],
                        "test_run_id": d['test_run_id']
                    },
                    'test_build': {
                        "id": d['test_build_id'],
                        "type": d['build_type'],
                        "version": d['product_version'],
                        "name": d['product_name'],
                        "branch": d['product_branch'],
                        "revision": d['revision'],
                    },
                    'push_info': {},
                    'pages':{}
                    }

            if d['page_name'] not in key_lookup[summary_key]['pages']:
                key_lookup[summary_key]['pages'][ d['page_name'] ] = {}

                threshold_test_run_ids.add( d['threshold_test_run_id'] )

                key_lookup[summary_key]['pages'][ d['page_name'] ]['threshold_revision'] = \
                    d['threshold_test_run_id']

            value_name = d['metric_value_name']
            value = d['value']

            value = self._format_value(value_name, value)

            if value_name in self.push_value_names:
                if value:
                    key_lookup[summary_key]['push_info'][value_name] = value

            key_lookup[summary_key]['pages'][ d['page_name'] ][value_name] = \
                value

        #Build a threshold revision lookup to return the threshold
        #revision str
        revision_lookup = self.get_threshold_revision_lookup(threshold_test_run_ids)

        #Replace the threshold_test_run_id with the associated revision str
        for key in key_lookup:
            for page in key_lookup[key]['pages']:
                threshold_test_run_id = key_lookup[key]['pages'][page]['threshold_revision']
                key_lookup[key]['pages'][page]['threshold_revision'] = \
                    revision_lookup[threshold_test_run_id]

        return key_lookup.values()

    def get_metrics_summary(self, test_run_ids):
        """
        Retrieve all metrics test evaluations associated with a given
        revision.

        returns the following dictionary:

            {
                product_info: {
                    "version": "15.0",
                    "name": "Firefox",
                    "branch": "Mozilla-Beta",
                    "revision": "ebfad1bf8749"
                    "push_date":123412341234,
                    "pushlog_id":12341234
                },

                summary: {
                    "total_tests": 2000,
                    "tests_missing_metrics": 3,
                    "pass":{value:1850, percent:"92.5%"},
                    "fail":{value:150, percent:"7.5%"}
                },
                "summary_by_test": {
                    "Talos Tp5row":{
                        total_tests:500,
                        pass:{
                            value:450, percent:"90%"
                            },
                        fail:{
                            value:50, percent:"10%"
                            },
                        }
                    },
                    ...
                },
                "summary_by_platform": {

                    "Linux x86_64 fedora 12": {
                        total_tests:500,
                        pass:{
                            value:450, percent:"90%"
                            },
                        fail:{
                            value:50, percent:"10%"
                            },
                        },
                        ...
                    }
                },

                tests:{

                    "Talos Tp5row":{
                                        "Linux x86_64 fedora 12": {
                                            total_tests:500,
                                            pass:{
                                                value:450, percent:"90%"
                                                },
                                            fail:{
                                                value:50, percent:"10%"
                                                },
                                            pages:[ { layers1.html:0,
                                                      layers2.html:1,
                                                      ... } ]
                                            }
                                   },
                        ...
                    }
             }
        """
        summary_data = {}

        if not test_run_ids:
            return summary_data

        r_string = ','.join( map( lambda tr_id: '%s', test_run_ids ) )

        proc = 'perftest.selects.get_test_evaluations_from_test_run_ids'

        computed_metrics = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            replace=[r_string],
            placeholders=test_run_ids,
            return_type='tuple'
            )

        if not computed_metrics:
            return summary_data

        key_lookup = set()

        ##Build a list of metric keys without trend data##
        keys_with_trend = set()
        keys_without_trend = set()
        threshold_test_run_ids = set()

        for d in computed_metrics:
            key = self.get_metrics_key(d)
            value_name = d['metric_value_name']
            value = int(d['value'])
            if (value_name == 'trend_mean') and (value > 0):
                keys_with_trend.add(key)

            threshold_test_run_ids.add( d['threshold_test_run_id'] )

        revision_lookup = self.get_threshold_revision_lookup(threshold_test_run_ids)

        summary_data = {
            'summary':self._get_counter_struct(),
            'summary_by_test':{},
            'summary_by_platform':{},
            'tests':{}
            }

        #Build summary data structure
        for d in computed_metrics:

            key = self.get_metrics_key(d)

            if key not in keys_with_trend:
                keys_without_trend.add(key)
                continue

            pname = "{0} {1} {2}".format(
                d['operating_system_name'],
                d['operating_system_version'],
                d['processor'],
                d['build_type'],
                )

            tname = d['test_name']

            if tname not in summary_data['tests']:
                summary_data['tests'][tname] = {}

            if pname not in summary_data['tests'][tname]:
                cstruct = self._get_counter_struct()
                cstruct['pages'] = {}
                cstruct['platform_info'] = {}
                summary_data['tests'][tname][pname] = cstruct

            if pname not in summary_data['summary_by_platform']:
                summary_data['summary_by_platform'][pname] = \
                    self._get_counter_struct()

            if tname not in summary_data['summary_by_test']:
                summary_data['summary_by_test'][tname] = \
                    self._get_counter_struct()

            value_name = d['metric_value_name']
            value = d['value']

            value = self._format_value(value_name, value)

            summary_data['tests'][tname][pname]['platform_info'] = {
                'operating_system_name':d['operating_system_name'],
                'processor':d['processor'],
                'type':d['build_type'],
                'operating_system_version':d['operating_system_version']
                }

            if d['page_name'] not in summary_data['tests'][tname][pname]['pages']:
                summary_data['tests'][tname][pname]['pages'][ d['page_name'] ] = \
                    {
                        'threshold_revision':revision_lookup[ d['threshold_test_run_id'] ],
                        'test_evaluation':None,
                        'mean':None,
                        'stddev':None,
                        'trend_mean':None,
                        'trend_stddev':None,
                        'p':None,
                        'h0_rejected':None,
                        'n_replicates':None
                    }

            summary_data['tests'][tname][pname]['pages'][ d['page_name'] ][
                value_name] = value

            if value_name != 'test_evaluation':
                continue

            #only count the test_evaluation data
            summary_data['summary']['total_tests'] += 1
            summary_data['summary_by_platform'][pname]['total_tests'] += 1
            summary_data['summary_by_test'][tname]['total_tests'] += 1
            summary_data['tests'][tname][pname]['total_tests'] += 1

            if value == 1:
                summary_data['summary_by_platform'][pname]['pass']['value'] += 1
                summary_data['summary_by_test'][tname]['pass']['value'] += 1
                summary_data['tests'][tname][pname]['pass']['value'] += 1
                summary_data['summary']['pass']['value'] += 1

            if value == 0:
                summary_data['summary_by_platform'][pname]['fail']['value'] += 1
                summary_data['summary_by_test'][tname]['fail']['value'] += 1
                summary_data['tests'][tname][pname]['fail']['value'] += 1
                summary_data['summary']['fail']['value'] += 1

        #Calculate percentages
        summary_data['summary']['fail']['percent'] = \
            self._calculate_percentage(
                summary_data['summary']['fail']['value'],
                summary_data['summary']['total_tests']
                )

        summary_data['summary']['pass']['percent'] = \
            self._calculate_percentage(
                summary_data['summary']['pass']['value'],
                summary_data['summary']['total_tests']
                )

        for test in summary_data['summary_by_test']:

            summary_data['summary_by_test'][test]['fail']['percent'] = \
                self._calculate_percentage(
                    summary_data['summary_by_test'][test]['fail']['value'],
                    summary_data['summary_by_test'][test]['total_tests']
                    )

            summary_data['summary_by_test'][test]['pass']['percent'] = \
                self._calculate_percentage(
                    summary_data['summary_by_test'][test]['pass']['value'],
                    summary_data['summary_by_test'][test]['total_tests']
                    )

        for test in summary_data['summary_by_platform']:

            summary_data['summary_by_platform'][test]['fail']['percent'] = \
                self._calculate_percentage(
                    summary_data['summary_by_platform'][test]['fail']['value'],
                    summary_data['summary_by_platform'][test]['total_tests']
                    )

            summary_data['summary_by_platform'][test]['pass']['percent'] = \
                self._calculate_percentage(
                    summary_data['summary_by_platform'][test]['pass']['value'],
                    summary_data['summary_by_platform'][test]['total_tests']
                    )

        for test in summary_data['tests']:
            for platform in summary_data['tests'][test]:
                summary_data['tests'][test][platform]['fail']['percent'] = \
                    self._calculate_percentage(
                        summary_data['tests'][test][platform]['fail']['value'],
                        summary_data['tests'][test][platform]['total_tests']
                        )

                summary_data['tests'][test][platform]['pass']['percent'] = \
                    self._calculate_percentage(
                        summary_data['tests'][test][platform]['pass']['value'],
                        summary_data['tests'][test][platform]['total_tests']
                        )

        summary_data['summary']['keys_without_trend'] = len(keys_without_trend)

        return summary_data

    def get_test_run_ids_from_pushlog_ids(self, pushlog_ids=[]):

        pushlog_ids.append(1)

        rep = []
        placeholders = []
        placeholders.extend(pushlog_ids)

        proc = 'perftest.selects.get_test_run_ids_from_pushlog_ids'

        test_run_ids = []

        if pushlog_ids:
            replace = ','.join( map( lambda pushlog_id: '%s', pushlog_ids ) )
            rep.append(replace)
            replace = [" ".join(rep)] if len(rep) else [" "]

            id_list = self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=self.DEBUG,
                replace=replace,
                placeholders=placeholders,
                return_type='tuple'
                )

            test_run_ids = [ test_data['test_run_id'] for test_data in id_list ]

        return test_run_ids

    def _format_value(self, value_name, value):

        if value_name == 'p':
            value = float( format(value, '.5f') )
        if value_name in self.format_float_values:
            value = float( format(value, '.1f') )
        if value_name in self.format_boolean_values:
            value = bool(value)

        return value

    def _calculate_percentage(self, value, total):

        percentage = 0.00
        if total > 0:
            percentage = round( (float(value)/float(total))*100.00 )
        return percentage

    def _get_counter_struct(self):

        return {
            'total_tests':0,
            'pass':{'value':0, 'percent':""},
            'fail':{'value':0, 'percent':""}
            }

    def get_metrics_data(self, revision):
        """
        Retrieve all metrics data associated with a given revision.

        returns the following dictionary:

            metric_key : {
                ref_data: {
                    all self.METRIC_KEYS: associated id,
                    test_run_id:id,
                    threshold_test_run_id:test_run_id of threshold used,
                    test_name:"Talos test name",
                    revision:revision
                },

                values : [ {
                    value:test value,
                    page_id:page_id,
                    metric_value_id:metric_value_id,
                    metric_value_name:metric_value_name
                    }, ...
                ]
            }
        """

        proc = 'perftest.selects.get_computed_metrics'

        computed_metrics = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=[revision],
            return_type='tuple'
            )

        key_lookup = {}
        for d in computed_metrics:
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

    def get_parent_test_data(
        self, pushlog, index, child_key, ref_data, metric_method_data=None
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
                revision = self.truncate_revision(parent_node['node'])

                #skip pushes without data
                if revision in self.skip_revisions:
                    continue

                data = self.get_test_values_by_revision(revision, ref_data)
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

    def run_metric_method(
        self, ref_data, child_data, parent_data, parent_metric_data={}
        ):

        m = self.mf.get_metric_method(ref_data['test_name'])
        results = m.run_metric_method(
            child_data, parent_data, parent_metric_data
            )
        return results

    def run_metric_summary(self, ref_data, data):

        m = self.mf.get_metric_method(ref_data['test_name'])
        results = m.run_metric_summary(data)
        return results

    def store_metric_results(
        self, revision, ref_data, results, threshold_test_run_id
        ):

        m = self.mf.get_metric_method(ref_data['test_name'])
        placeholders = m.get_data_for_metric_storage(
            ref_data, results, threshold_test_run_id
            )

        proc = 'perftest.inserts.set_test_page_metric'

        if placeholders:

            self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )
            if m.evaluate_metric_result(results):

                self.insert_or_update_metric_threshold(
                    revision,
                    ref_data,
                    m.get_metric_id()
                    )

    def store_metric_summary_results(
        self, revision, ref_data, results, metrics_data,
        threshold_test_run_id, parent_metrics_data={}
        ):

        proc = 'perftest.inserts.set_test_page_metric'

        m = self.mf.get_metric_method(ref_data['test_name'])

        placeholders = m.get_data_for_summary_storage(
            ref_data, results, metrics_data, threshold_test_run_id,
            parent_metrics_data
            )

        if placeholders:

            self.sources["perftest"].dhub.execute(
                proc=proc,
                debug_show=settings.DEBUG,
                placeholders=placeholders,
                executemany=True,
                )

    def insert_or_update_metric_threshold(
        self, revision, ref_data, metric_id
        ):

        proc = 'perftest.inserts.set_metric_threshold'

        placeholders = [

            ##Insert Placeholders
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            ref_data['build_type'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['test_run_id'],
            revision,

            ##Duplicate Key Placeholders
            ref_data['product_id'],
            ref_data['operating_system_id'],
            ref_data['processor'],
            ref_data['build_type'],
            metric_id,
            ref_data['test_id'],
            ref_data['page_id'],
            ref_data['test_run_id'],
            revision
            ]

        self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=settings.DEBUG,
            placeholders=placeholders
            )

    def load_test_data_all_dimensions(self, test_run_ids):

        if not test_run_ids:
            return {}

        ordered_columns = [
            'test_run_id',
            'product_id',
            'operating_system_id',
            'test_id',
            'page_id',
            'date_received',
            'revision',
            'product',
            'branch',
            'branch_version',
            'operating_system_name',
            'operating_system_version',
            'processor',
            'build_type',
            'machine_name',
            'pushlog_id',
            'push_date',
            'test_name',
            'page_url',
            'mean',
            'std',
            'h0_rejected',
            'p',
            'n_replicates',
            'fdr',
            'trend_mean',
            'trend_std',
            'test_evaluation'
            ]

        columns = {}
        for c in ordered_columns:
            columns[c] = None

        where_in_clause = ','.join( map( lambda v:'%s', test_run_ids ) )

        ####
        # Extract: Retrieve all available metrics data
        ###
        computed_metrics = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_test_evaluations_from_test_run_ids',
            debug_show=self.DEBUG,
            placeholders=test_run_ids,
            replace=[where_in_clause])

        aggregate_data = {}
        test_run_ids_with_metrics = set()

        # Transform data
        for d in computed_metrics:

            key = self.get_metrics_key(d)

            value_name = d['metric_value_name']

            if key not in aggregate_data:

                aggregate_data[ key ] = columns.copy()

                aggregate_data[key]['test_run_id'] = d['test_run_id']
                test_run_ids_with_metrics.add(d['test_run_id'])

                aggregate_data[key]['product_id'] = d['product_id']
                aggregate_data[key]['operating_system_id'] = d['operating_system_id']
                aggregate_data[key]['test_id'] = d['test_id']
                aggregate_data[key]['page_id'] = d['page_id']
                aggregate_data[key]['test_name'] = d['test_name']
                aggregate_data[key]['page_url'] = d['page_name']
                aggregate_data[key]['date_received'] = d['date']
                aggregate_data[key]['revision'] = d['revision']
                aggregate_data[key]['product'] = d['product_name']
                aggregate_data[key]['branch'] = d['product_branch']
                aggregate_data[key]['branch_version'] = d['product_version']
                aggregate_data[key]['operating_system_name'] = d['operating_system_name']
                aggregate_data[key]['operating_system_version'] = d['operating_system_version']
                aggregate_data[key]['processor'] = d['processor']
                aggregate_data[key]['build_type'] = d['build_type']
                aggregate_data[key]['machine_name'] = d['machine_name']

            if value_name == 'trend_stddev':
                #map column name
                aggregate_data[key]['trend_std'] = d['value']
            elif value_name == 'stddev':
                #map column name
                aggregate_data[key]['std'] = d['value']
            else:
                #The rest of the column names match, use value name
                #as the column name
                aggregate_data[key][value_name] = d['value']

        test_run_ids_set = set(test_run_ids)

        test_run_ids_no_metrics_data = test_run_ids_with_metrics.difference(
            test_run_ids_set)

        if not test_run_ids_with_metrics and not test_run_ids_no_metrics_data:
            test_run_ids_no_metrics_data = set( test_run_ids )

        ####
        # Extract:  If no metrics data is available for a test_run_id compute mean/std from
        # replicates
        ####
        if test_run_ids_no_metrics_data:

            where_in_clause = ','.join(
                map( lambda v:'%s', test_run_ids_no_metrics_data )
                )

            computed_mean = self.sources["perftest"].dhub.execute(
                proc='perftest.selects.get_test_run_value_full_summary',
                debug_show=self.DEBUG,
                placeholders=list(test_run_ids_no_metrics_data),
                replace=[where_in_clause])

            # Transform data
            for d in computed_mean:

                key = self.get_metrics_key(d)

                if key not in aggregate_data:

                    aggregate_data[key] = columns.copy()

                    aggregate_data[key]['test_run_id'] = d['test_run_id']
                    aggregate_data[key]['product_id'] = d['product_id']
                    aggregate_data[key]['operating_system_id'] = d['operating_system_id']
                    aggregate_data[key]['test_id'] = d['test_id']
                    aggregate_data[key]['page_id'] = d['page_id']
                    aggregate_data[key]['test_name'] = d['test_name']
                    aggregate_data[key]['page_url'] = d['page_name']
                    aggregate_data[key]['date_received'] = d['date']
                    aggregate_data[key]['revision'] = d['revision']
                    aggregate_data[key]['product'] = d['product_name']
                    aggregate_data[key]['branch'] = d['product_branch']
                    aggregate_data[key]['branch_version'] = d['product_version']
                    aggregate_data[key]['operating_system_name'] = d['operating_system_name']
                    aggregate_data[key]['operating_system_version'] = d['operating_system_version']
                    aggregate_data[key]['processor'] = d['processor']
                    aggregate_data[key]['build_type'] = d['build_type']
                    aggregate_data[key]['machine_name'] = d['machine_name']

                aggregate_data[key]['mean'] = d['mean']
                aggregate_data[key]['std'] = d['std']

        revisions_without_push_data = {}

        executemany_placeholders = []

        ####
        # Prepare data for loading
        ####
        for key in aggregate_data:

            placeholder_values = []
            for value in ordered_columns:
               placeholder_values.append( aggregate_data[key][value] )
            executemany_placeholders.append(placeholder_values)

            if not aggregate_data[key]['pushlog_id'] and \
                not aggregate_data[key]['push_date']:
                    revisions_without_push_data[ aggregate_data[key]['revision'] ] = \
                        aggregate_data[key]['branch']

        #####
        # Load data
        #####
        self.sources["perftest"].dhub.execute(
            proc='perftest.inserts.set_test_data_all_dimensions',
            debug_show=self.DEBUG,
            executemany=True,
            placeholders=executemany_placeholders)

        return revisions_without_push_data

    def get_data_all_dimensions(
        self, product, branch, os, os_version, test, page, start_time,
        stop_time):

        data = self.get_all_dimension_data_range(start_time, stop_time)

        column_value_map = [
            ['product', product],
            ['branch', branch],
            ['operating_system_name', os],
            ['operating_system_version', os_version],
            ['test_name', test],
            ['page_url', page]
            ]

        replace = ''
        placeholders = []

        for v in column_value_map:
            key = v[0]
            value = v[1]
            if value:
                replace += key + '= %s AND '
                placeholders.append(value)

        placeholders.append(data['start'])
        placeholders.append(data['stop'])

        data['data'] = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_test_data_all_dimensions',
            debug_show=self.DEBUG,
            placeholders=placeholders,
            replace=[replace])

        return data

    def get_platforms_and_tests(self, product, branch, date_begin, date_end):

        data = self.get_all_dimension_data_range(date_begin, date_end)

        data['data'] = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_all_dimensions_platforms_and_tests',
            debug_show=self.DEBUG,
            placeholders=[product, branch, data['start'], data['stop']])

        return data

    def get_all_dimension_data_range(self, date_begin, date_end):

        if not date_end:
            date_data = self.sources["perftest"].dhub.execute(
                proc='perftest.selects.get_max_all_dimensions_date',
                debug_show=self.DEBUG)

            if date_data:
                date_end = date_data[0]['max_date_received'] or int(time.time())
            else:
                date_end = int(time.time())

        if not date_begin:
            # default to 7 days if no time range is supplied
            date_begin = date_end - 604800

        data = {
            'min_date_data_received':"",
            'max_date_data_received':"",
            'data':[],
            'column_key':MetricsTestModel.ALL_DIMENSION_COLUMN_KEY
            }

        min_max_data = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_date_range_all_dimensions',
            debug_show=self.DEBUG)

        data['min_date_data_received'] = min_max_data[0]['min_date_data_received'] or date_begin
        data['max_date_data_received'] = min_max_data[0]['max_date_data_received'] or date_end

        data['start'] = date_begin
        data['stop'] = date_end

        return data

    def set_push_data_all_dimensions(self, revision_nodes):

        placeholders = []

        for revision in revision_nodes:

            if not revision_nodes[revision]:
                continue

            if 'alt_name' in revision_nodes[revision]:
                placeholders.append(
                    [ revision_nodes[revision]['pushlog_id'],
                      revision_nodes[revision]['date'],
                      revision,
                      revision_nodes[revision]['alt_name']
                        ]
                    )

            placeholders.append(
                [ revision_nodes[revision]['pushlog_id'],
                  revision_nodes[revision]['date'],
                  revision,
                  revision_nodes[revision]['name']
                    ]
                )

        proc = 'perftest.inserts.set_push_data_all_dimension'

        self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            executemany=True,
            )

    def log_msg(self, revision, test_run_id, msg_type, msg):

        proc = 'perftest.inserts.set_application_msg'

        placeholders = [ revision,
                         test_run_id,
                         msg_type,
                         msg,
                         int( time.time() )
                        ]

        self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            )

    def get_application_log(self, revision):

        proc = 'perftest.selects.get_application_log'

        placeholders = [ revision ]

        log = self.sources["perftest"].dhub.execute(
            proc=proc,
            debug_show=self.DEBUG,
            placeholders=placeholders,
            )

        return log

    def compute_inline_metrics(self, data):

        product = data['test_build']['name']
        branch = data['test_build']['branch']
        branch_version = data['test_build']['version']
        operating_system_name = data['test_build']['name']
        operating_system_version = data['test_machine']['osversion']
        processor = data['test_machine']['platform']
        test_name = data['testrun']['suite']

        pages = data['results'].keys()

        product_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_product_id',
            debug_show=self.DEBUG,
            placeholders=[product, branch, branch_version],
            return_type='iter',
            )
        product_id = product_iter.get_column_data('id')

        os_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_os_id',
            debug_show=self.DEBUG,
            placeholders=[operating_system_name, operating_system_version],
            return_type='iter',
            )
        os_id = os_iter.get_column_data('id')

        test_iter = self.sources["perftest"].dhub.execute(
            proc='perftest.selects.get_test_id',
            debug_show=self.DEBUG,
            placeholders=[test_name, 1],
            return_type='iter',
            )
        test_id = os_iter.get_column_data('id')

        ##Get the relevant ids##

        ##TODO: Finish this function or remove it

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

        metric_method.set_test_name(test_name)

        return metric_method

class MetricMethodInterface(object):
    """Defines the interface for metric methods to use"""

    MSG = (
        "Derived classes of MetricMethodBase should"
        "implement this function"
        )

    def run_metric_method(
        self, child_data, parent_data, parent_metric_data={}
        ):
        """
        Run the metric method and return results.

        child_data = [ test_value1, test_value2, test_value3, ... ]
        parent_data = [ test_value1, test_value2, test_value3, ... ]
        parent_metric_data = { metric_value_name: metric_value, ... }
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

            pushlog_id: Autoincremented id from pushlog table that
                corresponds to this revision,

            push_date: The data the push occurred,

            n_replicates: Number of replicates associated with the 
                metric datum,

            test_run_id:id,

            test_name:"Talos test name",

            revision:revision
            }

        result = The return value from run_metric_method.

        threshold_test_run_id = test_run_id used as threshold/parent.
        """
        raise NotImplementedError(self.MSG)

    def get_data_for_summary_storage(
        self, ref_data, results, metrics_data, threshold_test_run_id,
        parent_metrics_data={}
        ):
        """
        Get data for metric summary storage.  Should return a list of
        placeholders for perftest.inserts.set_test_page_metric

        ref_data = {
            all MetricsTestModel.METRIC_SUMMARY_KEYS: associated id,

            pushlog_id: Autoincremented id from pushlog table that
                corresponds to this revision,

            push_date: The data the push occurred,

            n_replicates: Number of replicates associated with the
                metric datum,

            test_run_id:id,

            test_name:"Talos test name",

            revision:revision
            }

        result = The return value from run_metric_summary_method.

        metrics_data = All metrics data associated with the datum.

        threshold_test_run_id = test_run_id used as threshold/parent.

        parent_metrics_data = The parents metrics data, defaults to {}
        """
        raise NotImplementedError(self.MSG)

class MetricMethodBase(MetricMethodInterface):
    """Base class for all metric methods"""

    def __init__(self, metric_collection):

        if not self.NAME:

            msg = (
                "Class, {0}, must set cls.NAME to a valid metric name "
                "found in the 'metric' table in the "
                "perftest schema"
                ).format(self.__class__.__name__)

            raise MetricMethodError(msg)

        if not self.SUMMARY_NAME:

            msg = (
                "Class, {0}, must set cls.SUMMARY_NAME to a valid "
                "metric value name found in the 'metric_value' table "
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

        self.test_name = ""

        self.set_metric_method()

    def set_metric_method(self):
        """
        Populates self.metric_id and self.metric_values for derived
        classes.  Requires derived classes set cls.NAME to a metric name
        found in the metric table in the perftest schema and
        cls.SUMMARY_NAME to a valid metric value name found in the
        'metric_value' table in the perftest schema or None if there is
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

    def set_test_name(self, test_name):
        self.test_name = test_name

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

    #Alpha value for ttests
    ALPHA = 0.05

    def __init__(self, metric_collection):

        super(TtestMethod, self).__init__(metric_collection)

        self.result_key = set([
            'p', 'h0_rejected', self.SUMMARY_NAME, 'pushlog_id',
            'push_date'
            ])

        #Store p value id for fdr
        self.metric_value_name = 'p'

    def get_start_index(self):
        start_index = 0
        if 'tp5' in self.test_name:
            start_index = 1
        return start_index

    def run_metric_method(
        self, child_data, parent_data, parent_metric_data={}
        ):

        trend_stddev = parent_metric_data.get('trend_stddev', None)
        trend_mean = parent_metric_data.get('trend_mean', None)

        #Some tests require filtering out the first replicate here
        start_index = self.get_start_index()

        if (trend_mean != None) and \
           (trend_mean > 0) and \
           (trend_stddev != None):

            #trend line data is available use it
            n = len(child_data[start_index:])
            s = std(child_data[start_index:], ddof=1)
            m = mean(child_data[start_index:])

            parent_n = len(parent_data[start_index:])
            trend_stddev = parent_metric_data['trend_stddev']
            trend_mean = parent_metric_data['trend_mean']

            p_value = welchs_ttest_internal(
                n, s, m, parent_n, trend_stddev, trend_mean
                )

            #Map results to output structure of welchs_ttest
            result = {
                "p": p_value,
                "stddev1":s,
                "stddev2":trend_stddev,
                "mean1":m,
                "mean2":trend_stddev,
                "h0_rejected":p_value < self.ALPHA
                }

        else:
            #No trend line data is available use the parent
            #replicate data

            result = welchs_ttest(
                child_data[start_index:],
                parent_data[start_index:],
                self.ALPHA
                )

        #####
        #If a divide by zero event occured the subsequent p value
        #will be numpy.nan, this will then be propagated through
        #all subsequent numerical treatments and stored in the database.
        #To prevent this from happening, raise a MetricMethodError for
        #any caller to catch.
        #####
        if isnan( result['p'] ):
            #p value is not a number
            msg = "p value is not a number, result:{0}".format(
                str(result)
                )

            raise MetricMethodError(msg)

        return result

    def run_metric_summary(self, data):

        filtered_data = self.filter_by_metric_value_name(data)
        rejector_data = rejector(filtered_data['values'])

        filtered_data['values']

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
            value = self.get_metric_value(
                metric_value_name, ref_data, result
                )

            if metric_value_name == 'h0_rejected':
                #Convert booleans to 0 or 1 for database storage
                value = int(value)

            if value == None:
                continue

            self._append_summary_placeholders(
                placeholders, test_run_id, metric_value_name, ref_data,
                value, threshold_test_run_id
            )

        return placeholders

    def get_data_for_summary_storage(
        self, ref_data, result, metrics_data, threshold_test_run_id,
        parent_data={}
        ):

        test_run_id = ref_data['test_run_id']

        placeholders = []

        for d in result:
            #Convert booleans to 0 or 1 for database storage
            value = int(d['value'])

            if value == None:
                continue

            #Load the summary data
            self._append_summary_placeholders(
                placeholders, test_run_id, self.SUMMARY_NAME, ref_data,
                value, threshold_test_run_id
            )

            #Evaluate whether the summary passes or not
            summary_pass = self.evaluate_metric_summary_result(
                { d['metric_value_name']: d['value'] }
                )

            #Retrieve required values
            lookup = self._get_summary_data_lookup(metrics_data)
            trend_mean = lookup.get('trend_mean', None)
            trend_stddev = lookup.get('trend_mean', None)

            #This variable represents whether the test passes or fails,
            #its value is ultimately determined by the results of
            #fdr.rejector.
            #
            #A test_evaluation of 0 indicates failure and 1 success
            test_evaluation = 0

            if summary_pass:
                #Summary test passes, update or initialize
                #trend line
                m_stddev = lookup.get('stddev', None)
                m_mean = lookup.get('mean', None)

                #Test passes set evaluation to success
                test_evaluation = 1

                n_replicates = ref_data['n_replicates']

                if (trend_mean != None) and \
                    (trend_mean > 0) and \
                    (trend_stddev != None):

                    #Update trend line
                    es_result = exp_smooth(
                        n_replicates, m_stddev, m_mean,
                        n_replicates, trend_stddev, trend_mean
                        )

                    trend_mean = es_result.get('mean', None)
                    trend_stddev = es_result.get('stddev', None)
                else:
                    #First time the t-test has been run for this metric
                    #datum, initialize the trend line
                    if parent_data:
                        p_lookup = self._get_summary_data_lookup(
                            parent_data
                            )

                        p_stddev = p_lookup.get('stddev', None)
                        p_mean = p_lookup.get('mean', None)

                        if (p_mean != None) and \
                            (p_stddev != None):

                            es_result = exp_smooth(
                                n_replicates, m_stddev, m_mean,
                                n_replicates, p_stddev, p_mean
                                )

                            trend_mean = es_result.get('mean', None)
                            trend_stddev = es_result.get('stddev', None)

            else:
               #Summary fails, store the parent trend values
               if parent_data:
                    parent_lookup = self._get_summary_data_lookup(
                        parent_data
                        )
                    trend_mean = parent_lookup.get('trend_mean', None)
                    trend_stddev = parent_lookup.get('trend_stddev', None)

            #If the trend_mean and trend_stddev are not set at this
            #point, there is no threshold trend to use and no parent
            #found
            if (trend_mean != None) and \
               (trend_mean > 0) and \
               (trend_stddev != None):

                #store trend mean
                self._append_summary_placeholders(
                    placeholders, test_run_id, 'trend_mean', ref_data,
                    trend_mean, threshold_test_run_id
                )

                #store trend stddev
                self._append_summary_placeholders(
                    placeholders, test_run_id, 'trend_stddev', ref_data,
                    trend_stddev, threshold_test_run_id
                )

            #store test_evaluation
            self._append_summary_placeholders(
                placeholders, test_run_id, 'test_evaluation', ref_data,
                test_evaluation, threshold_test_run_id
            )

        return placeholders

    def _append_summary_placeholders(
        self, placeholders, test_run_id, metric_value_name, ref_data,
        value, threshold_test_run_id
        ):

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

    def get_metric_value(self, metric_value_name, ref_data, result):

        value = None

        try:

            if metric_value_name in self.result_key:
                value = result[metric_value_name]

            else:
                value = result[metric_value_name + str(1)]

        except KeyError:

            #metric_value_name not in result, try the ref_data
            if metric_value_name in ref_data:
                value = ref_data[metric_value_name]
            return value

        else:
            return value


    def _get_summary_data_lookup(self, data):

        lookup = {}
        required_keys = set(
            ['trend_mean', 'trend_stddev', 'stddev', 'mean']
            )
        for key in required_keys:
            for d in data:
                if key == d['metric_value_name']:
                   lookup[key] = d['value']
                   break
        return lookup

class MetricMethodError(Exception):
    """
    Base class for all MetricMethod errors.  Takes an error message and
    returns string representation in __repr__.
    """
    def __init__(self, msg):
        self.msg = msg
    def __unicode__(self):
        return unicode(self.msg)

