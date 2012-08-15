import json

from django.http import HttpResponse

from datazilla.controller.admin.stats import perftest_stats, pushlog_stats
from .view_utils import get_range, REQUIRE_DAYS_AGO, API_CONTENT_TYPE

def get_not_referenced(request, project):
    """
    Return the testruns for a project in pushlogs not in datazilla.

    branches: optional.  The comma-separated list of branches to show data
        for.  If not provided, return data for all branches.
    days_ago: required.  Number of days ago for the "start" of the range.
    numdays: optional.  Number of days since days_ago.  Will default to
        "all since days ago"

    """
    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)
    range = get_range(request)
    branches = request.GET.get("branches", None)
    if branches:
        branches = branches.split(",")

    stats = pushlog_stats.get_not_referenced(
        project,
        range["start"],
        range["stop"],
        branches,
        )
    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_all_branches(request, project):
    """Get the full list of pushlog branches"""
    branches = pushlog_stats.get_all_branches()
    return HttpResponse(json.dumps(branches), content_type=API_CONTENT_TYPE)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = pushlog_stats.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), content_type=API_CONTENT_TYPE)
