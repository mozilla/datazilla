from django.core.exceptions import FieldError

from datazilla.model import factory


def get_runs_by_branch(project, startdate, enddate):
    """Return a list of test runs by branch in date range"""
    ptsm = factory.get_ptrdm(project)
    plm = factory.get_plm()

    branches = [x["name"] for x in plm.get_all_branches()]
    result = {}
    for branch in branches:
        test_runs = ptsm.get_run_lists_by_branch(startdate, enddate, branch)
        if test_runs["count"] > 0:
            result[branch] = test_runs

    plm.disconnect()
    ptsm.disconnect()
    return result


def get_run_counts_by_branch(project, startdate, enddate):
    """Return a count of test runs by branch in date range"""
    ptsm = factory.get_ptrdm(project)
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
    ptm = factory.get_ptm(project)
    result = get_ref_data_method(ptm, table)()
    ptm.disconnect()

    return result


def get_db_size(project):
    """Return the size of the database on disk in megabytes"""
    ptsm = factory.get_ptrdm(project)
    pt_size = ptsm.get_db_size()
    ptsm.disconnect()

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


