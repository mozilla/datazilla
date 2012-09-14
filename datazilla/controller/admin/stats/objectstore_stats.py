from datazilla.model.stats import PerformanceTestStatsModel


def get_error_count(project, startdate, enddate):
    """Return a count of all objectstore entries with error"""
    ptm = PerformanceTestStatsModel(project)
    err_counts = ptm.get_object_error_counts(startdate, enddate)
    ptm.disconnect()

    return err_counts


def get_error_list(project, startdate, enddate):
    """Return a list of all objectstore entries with errors in a date range"""
    ptm = PerformanceTestStatsModel(project)
    err_list = ptm.get_object_error_metadata(startdate, enddate)
    ptm.disconnect()
    return err_list


def get_json_blob(project, id):
    """Based on the ID passed in, return the JSON blob"""
    ptm = PerformanceTestStatsModel(project)
    blob = ptm.get_object_json_blob(id)
    ptm.disconnect()
    if blob:
        return blob[0]["json_blob"]
    else:
        return None


def get_error_detail_count(project, startdate, enddate):
    """Return counts attempting to parse some of the bad JSON to extract details."""
    ptm = PerformanceTestStatsModel(project)
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
    ptm = PerformanceTestStatsModel(project)
    size = ptm.get_db_size(source="objectstore")
    ptm.disconnect()
    return size

