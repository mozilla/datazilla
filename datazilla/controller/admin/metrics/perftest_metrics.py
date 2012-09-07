from datazilla.model import PushLogModel, MetricsTestModel
from datazilla.controller.admin.push_walker import extend_ref_data

def compute_test_run_metrics(project, pushlog_project, test_run_ids):

    ##
    #Get test data for test run ids
    ##
    plm = PushLogModel(pushlog_project)
    mtm = MetricsTestModel(project)

    #We don't know if we need the pushlog, make
    #sure to only retrieve once if we need it
    pushlog = None
    pushlog_lookup = {}

    for test_run_id in test_run_ids:

        child_test_data = mtm.get_test_values_by_test_run_id(test_run_id)

        push_node = None

        test_result = {}
        parent_data = {}
        cached_parent_data = {}

        for mkey in child_test_data:

            child_revision = child_test_data[mkey]['ref_data']['revision']

            #Get the pushlog node associated with this test_run_id
            if not push_node:
                branch = child_test_data[mkey]['ref_data']['branch']
                push_node = plm.get_node_from_revision(
                    child_revision, branch
                    )

            #Extend ref_data with push log info##
            extend_ref_data(child_test_data, mkey, push_node)

            #Get the threshold data if we have
            threshold_data = mtm.get_threshold_data(
                child_test_data[mkey]['ref_data']
                )

            if threshold_data:

                test_result = mtm.run_metric_method(
                    child_test_data[mkey]['ref_data'],
                    child_test_data[mkey]['values'],
                    threshold_data[mkey]['values'],
                    threshold_data[mkey]['metric_values'],
                    )

                mtm.store_metric_results(
                    child_revision,
                    child_test_data[mkey]['ref_data'],
                    test_result,
                    threshold_data[mkey]['ref_data']['test_run_id']
                    )

            else:
                #No threshold for the metrics datum
                #find a parent and initialize.  This is
                #either the first or second time this metrics
                #datum has been received.
                #
                # If it's the first, no parent will be found and
                # no metric data will be calculated.
                #
                # If it's the second, a parent will be found and
                # a full set of metrics data will be computed and
                # the threshold will be set.
                if not pushlog:
                    pushlog = plm.get_branch_pushlog(
                        push_node['branch_id'], 3, 0
                        )
                    _build_push_lookup(
                        mtm, pushlog, pushlog_lookup
                        )

                index = pushlog_lookup[child_revision]

                parent_data, test_result = mtm.get_parent_test_data(
                    pushlog, index, mkey, child_test_data[mkey]['values']
                    )

                if parent_data and test_result:
                    mtm.store_metric_results(
                        child_revision,
                        child_test_data[mkey]['ref_data'],
                        test_result,
                        parent_data['ref_data']['test_run_id']
                    )

            #Run summary metrics
            if test_result:

                child_metrics_data = mtm.get_metrics_data_from_ref_data(
                    child_test_data[mkey]['ref_data'], test_run_id
                    )

                extend_ref_data(child_metrics_data, mkey, push_node)

                summary_results = mtm.run_metric_summary(
                    child_metrics_data[mkey]['ref_data'],
                    child_metrics_data[mkey]['values']
                    )

                t_test_run_id = \
                    child_metrics_data[mkey]['ref_data']['threshold_test_run_id']

                if mkey in cached_parent_data:
                    parent_metrics_data = cached_parent_data[mkey]
                else:
                    parent_metrics_data = cached_parent_data.setdefault(
                        mkey,
                        mtm.get_metrics_data_from_ref_data(
                            child_metrics_data[mkey]['ref_data'],
                            t_test_run_id
                            )
                        )

                if mkey in parent_metrics_data:

                    mtm.store_metric_summary_results(
                        child_revision,
                        child_metrics_data[mkey]['ref_data'],
                        summary_results,
                        child_metrics_data[mkey]['values'],
                        child_metrics_data[mkey]['ref_data']['threshold_test_run_id'],
                        parent_metrics_data[mkey]['values']
                    )

                else:

                    mtm.store_metric_summary_results(
                        child_revision,
                        child_metrics_data[mkey]['ref_data'],
                        summary_results,
                        child_metrics_data[mkey]['values'],
                        child_metrics_data[mkey]['ref_data']['threshold_test_run_id']
                    )

    plm.disconnect()
    mtm.disconnect()

def _build_push_lookup(mtm, pushlog, pushlog_lookup):
    for index, node in enumerate(pushlog):
        pushlog_lookup[ mtm.truncate_revision( node['node'] ) ] = index
