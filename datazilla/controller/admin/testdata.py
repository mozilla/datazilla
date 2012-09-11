"""
Functions for fetching test data from a project.

"""
import json

from datazilla.model import factory

def get_testdata(project, branch, revision, os_name=None, test_name=None):
    """Return test data based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    ptsm = factory.get_ptsm(project)

    # get the testrun ids from perftest
    test_runs = ptm.get_test_run_ids(branch, revision, os_name, test_name)

    blobs = []
    for tr in test_runs:
        trid = tr["test_run_id"]
        blob = ptsm.get_object_json_blob_for_test_run(trid)[0]
        if blob["error_flag"] == "Y":
            blobs.append({"bad_test_data": {
                "test_run_id": trid,
                "error_msg": blob["error_msg"]
                }})
        else:
            blobs.append(json.loads(blob["json_blob"]))

    result = blobs
    return result


def get_metrics_data(project, branch, revision, os_name=None, test_name=None):
    """Return test data based on the parameters and optional filters."""

    ptm = factory.get_ptm(project)
    ptsm = factory.get_ptsm(project)

    # get the testrun ids from perftest
    test_runs = ptm.get_test_run_ids(branch, revision, os_name, test_name)

    #test page metric

    return {"CAUTION": "The metrics data you're about to enjoy may be hot."}
