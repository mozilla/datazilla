import traceback

from datazilla.model import PushLogModel, MetricsTestModel, MetricMethodError
from datazilla.model.utils import println
from datazilla.controller.admin.push_walker import extend_ref_data

SAFE_TESTS = set([
    'tp5', 'tsvg', 'tsvg_opacity', 'tdhtml', 'tdhtml_nochrome',
    'tsvgr'
    ])

def compute_test_run_metrics(project, pushlog_project, test_run_ids, debug):
    """
    Runs all metric tests and associated summaries on a list of test run ids
    """

    ##
    #Get test data for test run ids
    ##
    plm = PushLogModel(pushlog_project)
    mtm = MetricsTestModel(project)

    #####
    #We don't know if we need the pushlog, or for what branches
    #it will be required.  Make sure to only retrieve once for each
    #branch encountered and only when we need it.
    ####
    pushlog = {}

    #####
    #This data structure is used to lookup up the index position
    #of a revision in the push log to start walking from
    #####
    pushlog_lookup = {}

    for test_run_id in test_run_ids:

        child_test_data = mtm.get_test_values_by_test_run_id(test_run_id)

        if not child_test_data:
            msg = u"No test data available for test run id {0}".format(
                test_run_id
                )
            println(msg, debug)
            continue

        first_key = _get_first_mkey(child_test_data)

        rep_count = len(child_test_data[first_key]['values'])

        test_name = child_test_data[first_key]['ref_data']['test_name']

        child_revision, push_node, branch = _get_revision_and_push_node(
            plm, child_test_data, first_key
            )

        base_message = u"{0} {1}".format(child_revision, str(test_run_id))

        if not check_run_conditions(test_name, rep_count, push_node, debug):
            println(u"Not able to run {0}\n".format(base_message), debug)
            continue

        #The test and its replicates pass the run conditions
        println(u"Running {0}".format(base_message), debug)

        stored_metric_keys = []

        try:

            stored_metric_keys = _run_metrics(
                test_run_id, mtm, plm, child_test_data, pushlog,
                pushlog_lookup, child_revision, push_node, branch,
                test_name, debug
                )

        except Exception as e:

            _handle_exception(
                mtm, e, test_name, child_revision, test_run_id,
                compute_test_run_metrics.__name__, debug
                )

        try:

            _run_summary(
                test_run_id, mtm, plm, child_revision, child_test_data,
                stored_metric_keys, push_node, debug
                )

        except Exception as e:

            _handle_exception(
                mtm, e, test_name, child_revision, test_run_id,
                compute_test_run_metrics.__name__, debug
                )

        println(
            u"\tProcessing complete for {0}\n".format(base_message),
            debug
            )

    plm.disconnect()
    mtm.disconnect()

def run_test(test_name):
    """
    Confirm the base test string in the list of tests that can be processed
    by metrics tests is found in the test name provided.
    """
    execute_metrics = False
    for safe_test_base in SAFE_TESTS:
        if safe_test_base in test_name:
            execute_metrics = True
            break

    return execute_metrics

def check_run_conditions(test_name, rep_count, push_node, debug):
    """
    Test a set of conditions that have to be met in order to run the set of
    metrics tests.
    """
    #Confirm test name is in the safe test list
    if not run_test(test_name):
        println(u"Cannot run {0}".format(test_name), debug)
        return False

    if rep_count < 3:
        #If we don't have more than one replicate we cannot
        #run any of the existing metric tests
        println(
            u"Not enough replicates: {0} rep_count {1}".format(
                test_name, rep_count
                ),
            debug
            )
        return False

    if not push_node:
        #No push node found for this test run
        #we cannot proceed, need to log this
        println(u"No push node found", debug)
        return False

    return True

def _build_push_lookup(mtm, branch_id, pushlog, pushlog_lookup):
    for index, node in enumerate(pushlog[branch_id]):
        if branch_id not in pushlog_lookup:
            pushlog_lookup[ branch_id ] = {}
        pushlog_lookup[ branch_id ][ mtm.truncate_revision( node['node'] ) ] = index

def _get_revision_and_push_node(plm, data, first_key):

    revision = data[first_key]['ref_data']['revision']

    branch = data[first_key]['ref_data']['branch']

    #Get the pushlog node associated with this branch and revision
    push_node = plm.get_node_from_revision(
        revision, branch
    )

    return revision, push_node, branch

def _get_first_mkey(data):
    return data.keys()[0]

def _run_metrics(
    test_run_id, mtm, plm, child_test_data, pushlog, pushlog_lookup,
    child_revision, push_node, branch, test_name, debug
    ):
    """
    Run all metrics tests on the test_run_id provided.
    """

    println(u"\tStarting _run_metrics()", debug)

    stored_metric_keys = []

    for mkey in child_test_data:

        ####
        #Add push log data to the ref_data structure in child_metric_data
        #for storage.
        ###
        extend_ref_data(child_test_data, mkey, push_node)

        #Get the threshold data
        threshold_data = mtm.get_threshold_data(
           child_test_data[mkey]['ref_data']
           )

        if threshold_data:

            if debug:
                println(u"\tThreshold data found for metric datum", debug)
                println(u"\t\tCalling run_metric_method() with:", debug)

                println(
                    u"\t\tchild values:{0}".format(
                        str(child_test_data[mkey]['values'])
                        ),
                    debug
                    )

                println(
                    u"\t\tthreshold values:{0}".format(
                        str(threshold_data[mkey]['values'])
                        ),
                    debug
                    )

                println(
                    u"\t\tthreshold metric values:{0}".format(
                        str(threshold_data[mkey]['metric_values'])
                        ),
                    debug
                    )

            #Run the metric method
            try:
                test_result = mtm.run_metric_method(
                    child_test_data[mkey]['ref_data'],
                    child_test_data[mkey]['values'],
                    threshold_data[mkey]['values'],
                    threshold_data[mkey]['metric_values'],
                    )
            except MetricMethodError as e:
                ###
                #If we get an exception here, skip the test_run_id
                ###
                _handle_exception(
                    mtm, e, test_name, child_revision, test_run_id,
                    compute_test_run_metrics.__name__, debug
                    )

                continue

            if debug:
                #avoid formatting data if possible
                println(
                    u"\t\tStoring results:{0}".format(str(test_result)),
                    debug
                    )

            #Store the results
            mtm.store_metric_results(
                child_revision,
                child_test_data[mkey]['ref_data'],
                test_result,
                threshold_data[mkey]['ref_data']['test_run_id']
                )

            stored_metric_keys.append(mkey)

        else:
            #No threshold for the metrics datum
            #find a parent and initialize.  This is
            #either the first or second time this metrics
            #datum has been received.
            #
            # If it's the first, no parent will be found and
            # no metric data will be calculated.
            #
            # If it's the second, a parent will be found,
            # a full set of metrics data will be computed, and
            # the threshold will be set.
            branch_id = push_node['branch_id']

            if branch_id not in pushlog:
                pushlog[ branch_id ] = plm.get_branch_pushlog(
                    branch_id, 10, 0
                    )

                _build_push_lookup(
                    mtm, branch_id,
                    pushlog, pushlog_lookup
                    )

            if child_revision in pushlog_lookup[branch_id]:
                index = pushlog_lookup[branch_id][child_revision]
            else:
                #revision is not found in the pushlog, we cannot
                #proceed without an index at this point
                println(
                    u"\t\tRevision, {0}, not found in push log skipping".format(child_revision),
                    debug
                    )
                break

            if debug:
                println(
                    u"\t\tSearching pushlog for child: metric datum:{0}".format(mkey),
                    debug
                    )

                msg = u"\t\tPush log: branch:{0},".format(branch)
                msg = u"{0} index:{1} push log length:{2}".format(
                        msg, str(index), str(len(pushlog[ branch_id ]))
                        )

                println(msg, debug)

                println(
                    u"\t\tChild values provided:{0}".format(
                        str(child_test_data[mkey]['values'])
                        ),
                    debug
                    )

            ####
            #Walk the push log looking for a parent that passes the test
            #for the metric datum.
            ####
            parent_data, test_result = mtm.get_parent_test_data(
                pushlog[ branch_id ], index, mkey,
                child_test_data[mkey]['values']
            )

            if parent_data and test_result:

                if debug:
                    #avoid formatting data if possible
                    println(u"\t\tParent found in push log", debug)
                    println(
                        u"\t\ttest result:{0}".format( str(test_result) ),
                        debug
                        )

                ##Store the child data##
                mtm.store_metric_results(
                    child_revision,
                    child_test_data[mkey]['ref_data'],
                    test_result,
                    parent_data['ref_data']['test_run_id']
                    )

                stored_metric_keys.append(mkey)

                #The parent metric data needs to also be explicitly
                #stored, adapt the parent data from the test result
                parent_test_result = test_result.copy()

                parent_test_result['stddev1'] = test_result['stddev2']
                parent_test_result['mean1'] = test_result['mean2']

                parent_test_result['h0_rejected'] = \
                    test_result['h0_rejected']

                parent_test_result['p'] = test_result['p']

                parent_test_result['trend_stddev'] = test_result['stddev2']
                parent_test_result['trend_mean'] = test_result['mean2']

                if debug:
                    #avoid formatting data if possible
                    println(
                        u"\t\tStoring parent data: {0}".format(
                            str(parent_test_result)
                            ), debug
                            )

                mtm.store_metric_results(
                    parent_data['ref_data']['revision'],
                    parent_data['ref_data'],
                    parent_test_result,
                    parent_data['ref_data']['test_run_id']
                    )
            else:
                println(u"\t\tNo parent found", debug)

    return stored_metric_keys

def _run_summary(
    test_run_id, mtm, plm, child_revision, child_test_data,
    stored_metric_keys, push_node, debug
    ):

    println(u"\tStarting _run_summary()", debug)

    for mkey in stored_metric_keys:

        child_metrics_data = mtm.get_metrics_data_from_ref_data(
            child_test_data[mkey]['ref_data'], test_run_id
            )

        if not child_metrics_data:
            println(
                u"\t\tNo metrics data found for {0} {1}".format(
                    mkey, str(test_run_id)
                    ),
                debug
                )
            continue

        ####
        #Add push log data to the ref_data structure in child_metric_data
        #for storage.
        ###
        extend_ref_data(child_metrics_data, mkey, push_node)

        if debug:
            println(
                u"\t\tValues passed to metric summary:{0}".format(
                    str(child_metrics_data[mkey]['values'])
                    ),
                debug
                )

        summary_results = mtm.run_metric_summary(
            child_metrics_data[mkey]['ref_data'],
            child_metrics_data[mkey]['values']
            )

        if debug:
            println(
                u"\t\tSummary results:{0}".format(summary_results),
                debug
                )

        parent_metrics_data = mtm.get_metrics_data_from_ref_data(
            child_metrics_data[mkey]['ref_data'],
            child_metrics_data[mkey]['ref_data']['threshold_test_run_id']
            )

        if debug:
            println(
                u"\t\tStoring child summary values:{0}".format(
                    str(child_metrics_data[mkey]['values'])
                ),
                debug
                )

        if mkey in parent_metrics_data:

            if debug:
                println(
                    u"\t\tMetric datum key found in parent metrics data",
                    debug
                    )

                println(
                    u"\t\tparent data stored:{0}".format(
                        str(parent_metrics_data[mkey]['values'])
                        ),
                    debug
                    )

            mtm.store_metric_summary_results(
                child_revision,
                child_metrics_data[mkey]['ref_data'],
                summary_results,
                child_metrics_data[mkey]['values'],
                child_metrics_data[mkey]['ref_data']['threshold_test_run_id'],
                parent_metrics_data[mkey]['values']
                )

        else:

            println(
                u"\t\tMetric datum key NOT found in parent metrics data",
                debug
                )

            mtm.store_metric_summary_results(
                child_revision,
                child_metrics_data[mkey]['ref_data'],
                summary_results,
                child_metrics_data[mkey]['values'],
                child_metrics_data[mkey]['ref_data']['threshold_test_run_id']
                )

def _handle_exception(
    mtm, e, test_name, child_revision, test_run_id, msg_type,
    debug
    ):

    msg = u"{0}\nTest type: {1}\n Exception Name: {2}: {3}".format(
          traceback.format_exc(), test_name,
          e.__class__.__name__, unicode(e)
          )

    if debug:
        println(msg, debug)

    mtm.log_msg(
        child_revision,
        test_run_id,
        msg_type,
        msg
        )
