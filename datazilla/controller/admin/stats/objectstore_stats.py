import json

from datazilla.model import PerformanceTestModel


def get_count_errors(project):
    """Return a count of all objectstore entries with error"""
    ptm = PerformanceTestModel(project)
    err_counts = ptm.get_object_error_counts()
    ptm.disconnect()

    return err_counts


def get_list_errors(project, startdate, enddate):
    """Return a list of all objectstore entries with errors in a date range"""
    ptm = PerformanceTestModel(project)
    err_list = ptm.get_object_error_metadata()
    ptm.disconnect()
    return err_list


def get_json(id):
    """Based on the ID passed in, return the JSON blob"""
    raise NotImplementedError


def inspect_error_data(project):
    ptm = PerformanceTestModel(project)
    err_data = ptm.get_object_error_data()
    ptm.disconnect()

    counts = {}
    for item in err_data:
        tb = item["test_build"]
        counts[result_key(tb)] = counts.get(result_key(tb), 0) + 1
    return counts


def result_key(self, tb):
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
