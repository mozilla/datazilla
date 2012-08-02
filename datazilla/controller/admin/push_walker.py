"""
Functions for walking the push log and populating
the metrics schema

"""
import sys

from dzmetrics.ttest import welchs_ttest, fdr

from datazilla.model import PushLogModel, MetricsTestModel

def bootstrap(project):

    plm = PushLogModel('pushlog')

    mtm = MetricsTestModel(project)

    branches = plm.get_branch_list()

    for b in branches:

        if b['name'] in mtm.SPECIAL_HANDLING_BRANCHES:
            continue

        pushlog = plm.get_branch_pushlog( b['id'] )

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
            #CASE 1: No test data for the push, move on to the next push
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
                  in the push log so that if the immediate parent is not
                  available the child revision is skipped until the parent
                  is present.
                """
                mtm.skip_revision(revision)
                continue

            #Get the thresholds for the tests associated with this changeset
            for key in child_test_data:

                if key in computed_metrics_data:
                    #Metrics already computed
                    continue

                threshold_data = mtm.get_threshold_data(
                    child_test_data[key]['ref_data']
                    )

                if not threshold_data:
                    ###
                    # CASE 3: No threshold data exists for the metric datum
                    #   get the first parent with data.
                    #
                    # ASSUMPTION: The first parent with data is a viable
                    #   place to bootstrap the threshold value for the
                    #   metric datum.
                    ###
                    parent_data, test_result = mtm.get_parent_test_data(
                        pushlog, index, key, child_test_data[key]['values']
                        )

                    if parent_data and test_result:

                        mtm.store_test(
                            revision,
                            child_test_data[key]['ref_data'],
                            test_result
                            )

                    else:
                        continue
                else:

                    ###
                    #CASE 2: Threshold data exists for the metric datum.
                    #   Use it to run the test. 
                    ###
                    test_result = mtm.run_test(
                        child_test_data[key]['ref_data'],
                        child_test_data[key]['values'],
                        threshold_data[key]['values']
                        )

                    mtm.store_test(
                        revision,
                        child_test_data[key]['ref_data'],
                        test_result
                        )

                    #TODO: set the parent_test_data here
                    pass


    plm.disconnect()
    mtm.disconnect()

def summary(project):

    mtm = MetricsTestModel(project)
    plm = PushLogModel('pushlog')

    branches = plm.get_branch_list()

    for b in branches:

        if b['name'] in mtm.SPECIAL_HANDLING_BRANCHES:
            continue

        pushlog = plm.get_branch_pushlog( b['id'] )

        for index, node in enumerate( pushlog ):

            revision = mtm.get_revision_from_node(node['node'])

            #Get the test value data for this changeset
            test_data = mtm.get_test_values(revision, 'aggregate_ids')
            metrics_data = mtm.get_metrics_data(revision, 'aggregate_ids')

            for product_id in test_data:
                for os_id in test_data[product_id]:
                    for processor in test_data[product_id][os_id]:
                        for test_id in test_data[product_id][os_id][processor]:
                            print test_data[product_id][os_id][processor][test_id]


            #computed_metrics_data = mtm.get_metrics_data(revision)


    plm.disconnect()
    mtm.disconnect()

