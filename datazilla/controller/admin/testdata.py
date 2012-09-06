"""
Functions for fetching test data from a project.

"""
import json

from datazilla.model.base import PerformanceTestModel
from datazilla.model.stats import PerformanceTestStatsModel

def get_testdata(project, branch, revision,
    os_name=None, test_name=None):
    """Return test data based on the parameters and optional filters."""

    ptm = PerformanceTestModel(project)
    ptsm = PerformanceTestStatsModel(project)

    # get the testrun ids from perftest
    test_runs = ptm.get_test_run_ids(branch, revision, os_name, test_name)

    # get the json blobs matching those testrun ids
    id_list = [x["test_run_id"] for x in test_runs]

    blobs = []
    for tr in test_runs:
        trid = tr["test_run_id"]
        blob = ptsm.get_object_json_blob(trid)[0]
        blobs.append(json.loads(blob["json_blob"]))

    result = blobs
    return result