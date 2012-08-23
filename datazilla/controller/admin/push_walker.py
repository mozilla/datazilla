"""
Functions for walking the push log and populating
the metrics schema
"""
import sys

from datazilla.model import PushLogModel, MetricsTestModel

# Branches that require special handling
SPECIAL_HANDLING_BRANCHES = set(['Try'])

def run_metrics(project, options):
    """
        This function retrieves the push log for a given branch and
    iterates over each push in ascending order implementing the following
    rule set:

    1.) If a revision associated with a push node has no data in the
        perftest schema skip it.

    2.) If a revision associated with a push node already has metrics
        data associated with it in the perftest schema skip the metrics
        datums that already have data.

    3.) If test data is present for a revision assiociated with a push
        node, implement the following for all test data metric datums
        that have no associated metric data:

        3a.) If a threshold is present for a given metric datum,
             use the test data associated with it to compute the
             results of the associated metric method.  Store the
             metric test results.

             If the metric method test succeeds and the push date
             associated with the revision is greater than or equal
             to the threshold push date, update the threshold.

        3b.) If no threshold is present for a given metric datum,
             walk through consequtive pushes in the push log until
             a parent is found that passes the test associated with
             the metric datum's metric method.  Store the test
             results and the threshold associated with the metric
             datum.

        If the immediate parent push does not have data in datazilla this
    could be due to the assyncronous build/test environment sending data in
    a different order than the pushlog push order.  How do we distinguish
    between when this occurs and when the data has never been sent to
    datazilla for a particular push?  These two scenarios are
    indistiguishable given the information this system has access to.
        The algorithm implemented uses test run data associated with a
    metric threshold if it's available for a particular metric datum, even
    if that threshold is not associated with the parent push.  There are
    several edge cases that can occur in the build environment that cause a
    push found in the push log to never have performance test data
    generated.  Because of this we cannot assume every push will have a
    parent with test data.
        If the child push is from a date before the metric threshold its
    test results will not be used to update the threshold so the stored
    threshold data is always moving forward in time.
    """
    plm = PushLogModel(options['pushlog_project'])

    mtm = MetricsTestModel(project)

    branches = plm.get_branch_list()

    for b in branches:

        if b['name'] in SPECIAL_HANDLING_BRANCHES:
            continue

        pushlog = plm.get_branch_pushlog(
            b['id'], options['numdays'], options['daysago']
            )

        plen = len(pushlog)

        for index, node in enumerate(pushlog):

            revision = mtm.get_revision_from_node(node['node'])

            #Get the test value data for this revision
            child_test_data = mtm.get_test_values(revision)
            test_data_set = set(child_test_data.keys())

            ###
            #CASE: No test data for the push, move on to the next push
            ###
            if not child_test_data:
                """
                Keep track of pushes with no data so we can skip them
                when looking for parents
                """
                mtm.add_skip_revision(revision)
                continue

            #Get the computed metrics for this revision
            computed_metrics_data = mtm.get_metrics_data(revision)
            computed_metrics_set = set(computed_metrics_data.keys())

            ###
            #CASE: Revision could already have metrics associated with it.
            #   Use computed_metrics_data to exclude datums that have
            #   already had their metrics data calculated.
            ###
            data_without_metrics = test_data_set.difference(
                computed_metrics_set
                )

            for child_key in data_without_metrics:

                threshold_data = mtm.get_threshold_data(
                    child_test_data[child_key]['ref_data']
                    )

                if threshold_data:

                    ###
                    #CASE: Threshold data exists for the metric datum.
                    #   Use it to run the test.
                    ###
                    test_result = mtm.run_metric_method(
                        child_test_data[child_key]['ref_data'],
                        child_test_data[child_key]['values'],
                        threshold_data[child_key]['values']
                        )

                    mtm.store_metric_results(
                        revision,
                        child_test_data[child_key]['ref_data'],
                        test_result,
                        pushlog[index]['date'],
                        threshold_data[child_key]['ref_data']['push_date'],
                        threshold_data[child_key]['ref_data']['test_run_id']
                        )
                else:

                    ###
                    # CASE: No threshold data exists for the metric datum
                    #   get the first parent with data.
                    #
                    # ASSUMPTION: The first parent with data is a viable
                    #   place to bootstrap the threshold value for the
                    #   metric datum.
                    ###

                    parent_data, test_result = mtm.get_parent_test_data(
                        pushlog, index, child_key,
                        child_test_data[child_key]['values']
                        )

                    if parent_data and test_result:
                        mtm.store_metric_results(
                            revision,
                            child_test_data[child_key]['ref_data'],
                            test_result,
                            pushlog[index]['date'],
                            None,
                            parent_data['ref_data']['test_run_id']
                            )

    plm.disconnect()
    mtm.disconnect()

def summary(project, options):
    """
        This function retrieves the push log for a given branch and
    iterates over each push in ascending order implementing the following
    ruleset:

    1.) If no metrics data is associated with the revision skip it.

    2.) For tests associated with a given revision, retrieve metric datums
        that do not have metric method summary data associated with them.

    3.) Run the metric method summary and store the results.
    """

    mtm = MetricsTestModel(project)
    plm = PushLogModel(options['pushlog_project'])

    branches = plm.get_branch_list()

    for b in branches:

        if b['name'] in SPECIAL_HANDLING_BRANCHES:
            continue

        pushlog = plm.get_branch_pushlog(
            b['id'], options['numdays'], options['daysago']
            )

        for index, node in enumerate( pushlog ):

            revision = mtm.get_revision_from_node(node['node'])

            #Get the metric value data for this revision
            metrics_data = mtm.get_metrics_data(revision)

            #If there's no metric data a summary cannot be computed
            if not metrics_data:
                continue

            #Filter out tests that have had their summary computed
            store_list = get_test_keys_for_storage(mtm, metrics_data)

            for test_key in store_list:

                ############
                # ASSUMPTION: All of the metric values for each
                # page in the test are computed.  This is currently
                # true do to the requirements of the incoming JSON data
                # for a given test run.
                ###########
                results = mtm.run_metric_summary(
                    metrics_data[test_key]['ref_data'],
                    metrics_data[test_key]['values']
                    )

                mtm.store_metric_summary_results(
                    revision,
                    metrics_data[test_key]['ref_data'],
                    results,
                    metrics_data[test_key]['ref_data']['threshold_test_run_id'],
                    )

    plm.disconnect()
    mtm.disconnect()

def get_test_keys_for_storage(mtm, metrics_data):

    store_list = set()

    for test_key in metrics_data:

        summary_name = mtm.get_metric_summary_name(
            metrics_data[test_key]['ref_data']['test_name']
            )

        store = True

        for v in metrics_data[test_key]['values']:
            name = v.get('metric_value_name', None)
            #If the metric_value_name matches the summary
            #the summary has already been computed
            if summary_name in name:
                store = False
                break
        if store:
            store_list.add(test_key)

    return store_list
