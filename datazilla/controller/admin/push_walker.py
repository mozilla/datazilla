"""
Functions for walking the push log and populating
the metrics schema

"""
import sys

from datazilla.model import PushLogModel, MetricsTestModel

# Branches that require special handling
SPECIAL_HANDLING_BRANCHES = set(['Try'])

def run_metrics(project, options):

    plm = PushLogModel('pushlog')

    mtm = MetricsTestModel(project)

    branches = plm.get_branch_list()

    for b in branches:

        if b['name'] in SPECIAL_HANDLING_BRANCHES:
            continue

        pushlog = plm.get_branch_pushlog(
            b['id'], options['numdays'], options['daysago']
            )

        for index, node in enumerate( pushlog ):

            revision = mtm.get_revision_from_node(node['node'])

            #Get the test value data for this changeset
            child_test_data = mtm.get_test_values(revision)

            ###
            #CASE: Revision could already have metrics associated with it.
            #   Use computed_metrics_data as a lookup to see what has
            #   already been calculated.
            ###
            computed_metrics_data = mtm.get_metrics_data(revision)

            ###
            #CASE: No test data for the push, move on to the next push
            ###
            if not child_test_data:
                """
                Keep track of pushes with no data so we can skip them
                when looking for parents

                DANGER: If the immediate parent push does not
                  have data in datazilla this could be due to the
                  assyncronous build/test environment sending data in a
                  different order than the pushlog push order.
                      How do we distinguish between when this occurs
                  and when the data has never been sent to datazilla for a
                  particular push?
                      This needs to be ressolved, otherwise there is a
                  chance we will be using the wrong parent.
                      The best solution would be to have enough confidence
                  in the push log coverage in the perftest schema so that if
                  the immediate parent is not available the child revision
                  is skipped until the parent is present.
                """
                mtm.add_skip_revision(revision)
                continue

            #Test data found, get the metric thresholds for the tests
            #associated with this changeset
            for child_key in child_test_data:

                if child_key in computed_metrics_data:
                    #Metrics already computed for the datum
                    continue

                threshold_data = mtm.get_threshold_data(
                    child_test_data[child_key]['ref_data']
                    )

                if not threshold_data:
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
                            test_result
                            )

                    else:
                        continue
                else:

                    ###
                    #CASE 2: Threshold data exists for the metric datum.
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
                        test_result
                        )


    plm.disconnect()
    mtm.disconnect()

def summary(project, options):

    mtm = MetricsTestModel(project)
    plm = PushLogModel('pushlog')

    branches = plm.get_branch_list()

    for b in branches:

        if b['name'] in SPECIAL_HANDLING_BRANCHES:
            continue

        pushlog = plm.get_branch_pushlog(
            b['id'], options['numdays'], options['daysago']
            )

        for index, node in enumerate( pushlog ):

            revision = mtm.get_revision_from_node(node['node'])
            #Get the metric value data for this changeset
            metrics_data = mtm.get_metrics_data(revision)

            #If there's no metric data a summary cannot be computed
            if not metrics_data:
                continue

            #Filter out tests that have had their summary computed
            store_list = get_test_keys_for_storage(mtm, metrics_data)

            for test_key in store_list:

                ############
                # ASSUMPTION: If we have a test_id in the
                # metrics data all of the metric values for each
                # page in the test are computed.
                ###########
                results = mtm.run_metric_summary(
                    metrics_data[test_key]['ref_data'],
                    metrics_data[test_key]['values']
                    )

                mtm.store_metric_summary_results(
                    revision,
                    metrics_data[test_key]['ref_data'],
                    results
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
