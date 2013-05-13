"""
Functions for fetching test data from a project.

"""
import json

from datazilla.model import factory
from datazilla.model import utils

def get_testdata(
    project, branch, revision, product_name=None, os_name=None,
    os_version=None, branch_version=None, processor=None,
    build_type=None, test_name=None, page_name=None):
    """Return test data based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    ptrdm = factory.get_ptrdm(project)

    # get the testrun ids from perftest
    test_run_ids = ptm.get_test_run_ids(
        branch, [revision], product_name, os_name, os_version,
        branch_version, processor, build_type, test_name
        )

    blobs = ptrdm.get_object_json_blob_for_test_run(test_run_ids)

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
    ptrdm.disconnect()

    return filtered_blobs


def get_metrics_data(
    project, branch, revision, product_name=None, os_name=None,
    os_version=None, branch_version=None, processor=None, build_type=None,
    test_name=None, page_name=None
    ):
    """Return metrics data based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    mtm = factory.get_mtm(project)

    # get the testrun ids from perftest
    test_run_ids = ptm.get_test_run_ids(
        branch, [revision], product_name, os_name, os_version,
        branch_version, processor, build_type, test_name
        )

    #test page metric
    metrics_data = mtm.get_metrics_data_from_test_run_ids(
        test_run_ids, page_name
        )

    ptm.disconnect()
    mtm.disconnect()

    return metrics_data

def get_metrics_summary(
    project, branch, revision, product_name=None, os_name=None,
    os_version=None, branch_version=None, processor=None, build_type=None,
    test_name=None, pushlog_project=None
    ):
    """Return a metrics summary based on the parameters and optional filters."""

    plm = factory.get_plm(pushlog_project)
    ptm = factory.get_ptm(project)
    mtm = factory.get_mtm(project)

    # get the testrun ids from perftest
    test_run_ids = ptm.get_test_run_ids(
        branch, [revision], product_name, os_name, os_version,
        branch_version, processor, build_type, test_name
        )

    #test page metric
    metrics_data = mtm.get_metrics_summary(test_run_ids)

    metrics_data['product_info'] = {
        'version': branch_version,
        'name': product_name,
        'branch': branch,
        'revision': revision
        }

    #get push info
    push_data = plm.get_node_from_revision(revision, branch)
    metrics_data['push_data'] = push_data

    #get the products associated with this revision/branch combination
    products = ptm.get_revision_products(revision, branch)
    metrics_data['products'] = products

    plm.disconnect()
    ptm.disconnect()
    mtm.disconnect()

    return metrics_data

def get_metrics_pushlog(
    project, branch, revision, product_name=None, os_name=None,
    os_version=None, branch_version=None, processor=None, build_type=None,
    test_name=None, page_name=None, pushes_before=None, pushes_after=None,
    pushlog_project=None
    ):
    """Return a metrics summary based on the parameters and optional filters."""

    plm = factory.get_plm(pushlog_project)
    ptm = factory.get_ptm(project)
    mtm = factory.get_mtm(project)

    aggregate_pushlog, changeset_lookup = plm.get_branch_pushlog_by_revision(
        revision, branch, pushes_before, pushes_after
        )

    pushlog_id_index_map = {}
    all_revisions = []

    for index, node in enumerate(aggregate_pushlog):

        pushlog_id_index_map[node['pushlog_id']] = index

        aggregate_pushlog[index]['metrics_data'] = []
        aggregate_pushlog[index]['dz_revision'] = ""
        aggregate_pushlog[index]['branch_name'] = branch

        changesets = changeset_lookup[ node['pushlog_id'] ]

        #The revisions associated with a push are returned in reverse order
        #from the pushlog web service.  This orders them the same way tbpl
        #does.
        changesets['revisions'].reverse()

        #truncate the revision strings and collect them
        for cset_index, revision_data in enumerate(changesets['revisions']):

            full_revision = revision_data['revision']

            revision = mtm.truncate_revision(full_revision)
            changesets['revisions'][cset_index]['revision'] = revision

            all_revisions.append(revision)

        aggregate_pushlog[index]['revisions'] = changesets['revisions']


    pushlog_id_list = pushlog_id_index_map.keys()

    # get the testrun ids from perftest
    filtered_test_run_ids = ptm.get_test_run_ids(
        branch, all_revisions, product_name, os_name, os_version,
        branch_version, processor, build_type, test_name
        )

    # get the test run ids associated with the pushlog ids
    pushlog_test_run_ids = mtm.get_test_run_ids_from_pushlog_ids(
        pushlog_ids=pushlog_id_list
        )

    # get intersection
    test_run_ids = list( set(filtered_test_run_ids).intersection(
        set(pushlog_test_run_ids)) )

    # get the metrics data for the intersection
    metrics_data = mtm.get_metrics_data_from_test_run_ids(
        test_run_ids, page_name
        )

    #decorate aggregate_pushlog with the metrics data
    for d in metrics_data:

        pushlog_id = d['push_info'].get('pushlog_id', None)

        #A defined pushlog_id is required to decorate the correct push
        if not pushlog_id:
            continue

        pushlog_index = pushlog_id_index_map[pushlog_id]
        aggregate_pushlog[pushlog_index]['metrics_data'].append(d)
        aggregate_pushlog[pushlog_index]['dz_revision'] = d['test_build']['revision']

    plm.disconnect()
    ptm.disconnect()
    mtm.disconnect()

    return aggregate_pushlog

def get_application_log(project, revision):

    mtm = factory.get_mtm(project)
    log = mtm.get_application_log(revision)
    return log

def get_default_version(project, branch, product_name):

    ptm = factory.get_ptm(project)

    default_version = ptm.get_default_branch_version(
        branch, product_name
        )

    ptm.disconnect()

    version = ""
    if 'version' in default_version:
        version = default_version['version']

    return version

def get_test_value_summary(project, branch, test_ids, url, begin, now):

    ptm = factory.get_ptm(project)

    data = ptm.get_value_summary_by_test_ids(
        branch, test_ids, url, begin, now
        )

    ptm.disconnect()

    return data

def get_test_data_all_dimensions(project, min_timestamp, max_timestamp):

    mtm = factory.get_mtm(project)
    data = mtm.get_data_all_dimensions(min_timestamp, max_timestamp)
    mtm.disconnect()

    return data


