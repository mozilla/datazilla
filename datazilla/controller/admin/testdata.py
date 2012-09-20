"""
Functions for fetching test data from a project.

"""
import json

from datazilla.model import factory

def get_testdata(
    project, branch, revision, os_name=None, os_version=None,
    processor=None, build_type=None, test_name=None, page_name=None):
    """Return test data based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    ptsm = factory.get_ptsm(project)

    # get the testrun ids from perftest
    test_run_ids = ptm.get_test_run_ids(
        branch, revision, os_name, os_version, processor, build_type,
        test_name
        )

    blobs = ptsm.get_object_json_blob_for_test_run(test_run_ids)

    filtered_blobs = []

    #Build a page lookup to filter by
    page_names = set()
    if page_name:
        map( lambda page:page_names.add(page.strip()), page_name.split(',') )

    for blob in blobs:
        if blob["error_flag"] == "Y":
            filtered_blobs.append({"bad_test_data": {
                "test_run_id": trid,
                "error_msg": blob["error_msg"]
                }})
        else:
            filtered_blob = json.loads(blob["json_blob"])

            #Only load pages in page_names
            if page_names:
                new_results = {}
                for p in page_names:
                    if p in filtered_blob['results']:
                        new_results[p] = filtered_blob['results'][p]
                filtered_blob['results'] = new_results

            filtered_blobs.append( filtered_blob )

    ptm.disconnect()
    ptsm.disconnect()

    return filtered_blobs


def get_metrics_data(
    project, branch, revision, os_name=None, os_version=None,
    processor=None, build_type=None, test_name=None, page_name=None
    ):
    """Return metrics data based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    mtm = factory.get_mtm(project)

    # get the testrun ids from perftest
    test_run_ids = ptm.get_test_run_ids(
        branch, revision, os_name, os_version, processor, build_type,
        test_name
        )

    #test page metric
    metrics_data = mtm.get_metrics_data_from_test_run_ids(
        test_run_ids, page_name
        )

    ptm.disconnect()
    mtm.disconnect()

    return metrics_data

def get_metrics_summary(
    project, branch, revision, os_name=None, os_version=None,
    processor=None, build_type=None, test_name=None
    ):
    """Return a metrics summary based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    mtm = factory.get_mtm(project)

    # get the testrun ids from perftest
    test_run_ids = ptm.get_test_run_ids(
        branch, revision, os_name, os_version, processor, build_type,
        test_name
        )

    #test page metric
    metrics_data = mtm.get_metrics_summary(test_run_ids)

    ptm.disconnect()
    mtm.disconnect()

    return metrics_data

def get_metrics_trend(
    project, branch, os_name=None, os_version=None, processor=None,
    build_type=None, test_name=None, page_name=None, days_ago=None,
    numdays=None
    ):
    """Return a metrics summary based on the parameters and optional filters."""

    plm = factory.get_plm()
    ptm = factory.get_ptm(project)
    mtm = factory.get_mtm(project)

    pushlog = plm.get_branch_pushlog(None, days_ago, numdays, branch)

    aggregate_pushlog = []
    pushlog_id_index_map = {}

    for node in pushlog:
        revision = mtm.truncate_revision(node['node'])
        if node['pushlog_id'] not in pushlog_id_index_map:
            node_struct = {
                    'revisions':[],
                    'dz_revision':"",
                    'branch_name':node['name'],
                    'date':node['date'],
                    'push_id':node['push_id'],
                    'metrics_data':[]
                    }

            aggregate_pushlog.append(node_struct)
            index = len(aggregate_pushlog) - 1
            pushlog_id_index_map[node['pushlog_id']] = index

        pushlog_index = pushlog_id_index_map[ node['pushlog_id'] ]
        aggregate_pushlog[index]['revisions'].append(revision)

    pushlog_id_list = pushlog_id_index_map.keys()

    # get the testrun ids from perftest
    filtered_test_run_ids = ptm.get_test_run_ids(
        branch, None, os_name, os_version, processor, build_type,
        test_name, page_name
        )

    pushlog_test_run_ids = mtm.get_test_run_ids_from_pushlog_ids(
        pushlog_ids=pushlog_id_list
        )

    test_run_ids = list( set(filtered_test_run_ids).intersection(
        set(pushlog_test_run_ids)) )

    metrics_data = mtm.get_metrics_data_from_test_run_ids(
        test_run_ids, page_name
        )

    #decorate aggregate_pushlog with the trend data
    for d in metrics_data:
        pushlog_id = d['push_info']['pushlog_id']
        index = pushlog_id_index_map[pushlog_id]
        aggregate_pushlog[index]['metrics_data'].append(d)
        aggregate_pushlog[index]['dz_revision'] = d['test_build']['revision']

    plm.disconnect()
    ptm.disconnect()
    mtm.disconnect()

    return aggregate_pushlog

def get_application_log(project, revision):

    mtm = factory.get_mtm(project)
    log = mtm.get_application_log(revision)
    return log

