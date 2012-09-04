from django.core.exceptions import FieldError

from datazilla.model.stats import PerformanceTestStatsModel
from datazilla.model.base import PerformanceTestModel, PushLogModel
from pushlog_stats import get_all_branches


def get_ptsm(project):
    """
    Shortcut to return the PerformanceTestStatsModel.

    Allows the unit tests to override this to give the test version of the
    model.
    """
    return PerformanceTestStatsModel(project)


def get_ptm(project):
    """
    Shortcut to return the PerformanceTestModel.

    Allows the unit tests to override this to give the test version of the
    model.
    """
    return PerformanceTestModel(project)


def get_plm():
    """
    Hook to return a pushlog model.

    Handy for tests to mock out.
    """
    return PushLogModel()


def get_runs_by_branch(project, startdate, enddate):
    """Return a list of test runs by branch in date range"""
    ptsm = get_ptsm(project)
    branches = [x["name"] for x in get_plm().get_all_branches()]
    result = {}
    for branch in branches:
        test_runs = ptsm.get_run_lists_by_branch(startdate, enddate, branch)
        if len(test_runs) > 0:
            result[branch] = {
                "count": len(test_runs),
                "test_runs": test_runs,
                }

    ptsm.disconnect()
    return result


def get_run_counts_by_branch(project, startdate, enddate):
    """Return a count of test runs by branch in date range"""
    ptsm = get_ptsm(project)
    test_runs = ptsm.get_run_counts_by_branch(startdate, enddate)
    ptsm.disconnect()

    #now form the data the way we want it
    result = {}
    for tr in test_runs:
        branch = result.setdefault(tr["branch"], {})
        branch["count"] = tr.get("count")

    return result


def get_ref_data(project, table):
    """Return a simple list of data from ``table`` for ``project``."""
    ptm = get_ptm(project)
    result = get_ref_data_method(ptm, table)()
    ptm.disconnect()

    return result


def get_db_size(project):
    """Return the size of the database on disk in megabytes"""
    ptm = get_ptsm(project)
    pt_size = ptm.get_db_size()
    ptm.disconnect()

    return pt_size


def get_ref_data_method(ptm, table):
    """Return the matching model method for the ``table``."""
    methods = {
        "machines": ptm.get_machines,
        "operating_systems": ptm.get_operating_systems,
        "options": ptm.get_options,
        "tests": ptm.get_tests,
        "pages": ptm.get_pages,
        "products": ptm.get_products
        }
    try:
        return methods[table]

    except KeyError:
        raise FieldError(
            "Not a supported ref_data table.  Must be in: {0}".format(
                methods.keys()))


