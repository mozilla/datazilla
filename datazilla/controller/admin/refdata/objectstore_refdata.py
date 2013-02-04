from datazilla.model.refdata import PerformanceTestRefDataModel
from datazilla.model.base import PerformanceTestModel


def get_error_count(project, startdate, enddate):
    """Return a count of all objectstore entries with error"""
    ptm = PerformanceTestRefDataModel(project)
    err_counts = ptm.get_object_error_counts(startdate, enddate)
    ptm.disconnect()

    return err_counts


def get_error_list(project, startdate, enddate):
    """Return a list of all objectstore entries with errors in a date range"""
    ptm = PerformanceTestRefDataModel(project)
    err_list = ptm.get_object_error_metadata(startdate, enddate)
    ptm.disconnect()
    return err_list


def get_json_blob(project, id):
    """Based on the ID passed in, return the JSON blob"""
    ptm = PerformanceTestRefDataModel(project)
    blob = ptm.get_object_json_blob(id)
    ptm.disconnect()

    if blob:
        return blob[0]

    return {}

def get_json_blob_by_test_run_id(project, test_run_id):
    """Based on the test_run_id passed in, return the JSON blob"""
    ptm = PerformanceTestRefDataModel(project)
    blob = ptm.get_object_json_blob_for_test_run([test_run_id])
    ptm.disconnect()

    if blob:
        return blob[0]

    return {}

def get_json_blob_by_revisions(
    project, branch, gaia_revision, gecko_revision, testId):

    ptm = PerformanceTestModel(project)
    test_run_ids = ptm.get_test_run_ids_by_revisions(
        branch, gaia_revision, gecko_revision, testId
        )
    ptm.disconnect()

    ptrm = PerformanceTestRefDataModel(project)
    blobs = ptrm.get_object_json_blob_for_test_run(test_run_ids)
    ptm.disconnect()

    return blobs

def get_error_detail_count(project, startdate, enddate):
    """Return counts attempting to parse some of the bad JSON to extract details."""
    ptm = PerformanceTestRefDataModel(project)
    err_data = ptm.get_parsed_object_error_data(startdate, enddate)
    ptm.disconnect()

    counts = {}
    for item in err_data:
        tb = item["test_build"]
        counts[result_key(tb)] = counts.get(result_key(tb), 0) + 1
    return counts


def result_key(tb):
    """Build a key based on the fields of tb."""
    try:
        key = "{0} - {1} - {2}".format(
            tb["name"],
            tb["branch"],
            tb["version"],
            )

    except KeyError:
        key = "unknown"

    return key


def get_db_size(project):
    """Return the size of the objectstore database on disk in MB."""
    ptm = PerformanceTestRefDataModel(project)
    size = ptm.get_db_size(source="objectstore")
    ptm.disconnect()
    return size

