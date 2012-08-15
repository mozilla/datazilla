import json

from django.http import HttpResponse

from datazilla.controller.admin.stats import perftest_stats
from .view_utils import get_range, REQUIRE_DAYS_AGO, API_CONTENT_TYPE


def get_runs_by_branch(request, project):
    """
    Return the testruns for a project broken down by branches.

    days_ago: required.  Number of days ago for the "start" of the range.
    numdays: optional.  Number of days since days_ago.  Will default to
        "all since days ago"

    """
    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)

    range = get_range(request)

    if request.GET.get("show_test_runs"):
        stats = perftest_stats.get_runs_by_branch(
            project,
            range["start"],
            range["stop"],
            )
    else:
        stats = perftest_stats.get_run_counts_by_branch(
            project,
            range["start"],
            range["stop"],
            )

    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_ref_data(request, project, table):
    """Get simple list of ref_data for ``table`` in ``project``"""
    stats = perftest_stats.get_ref_data(project, table)
    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = perftest_stats.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), content_type=API_CONTENT_TYPE)
