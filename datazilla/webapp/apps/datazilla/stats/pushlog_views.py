import json

from django.http import HttpResponse

from datazilla.controller.admin.stats import perftest_stats, pushlog_stats
from datazilla.model import utils

APP_JS = 'application/json'

def get_not_referenced(request, project):
    """
    Return the testruns for a project in pushlogs not in datazilla.

    branches: optional.  The comma-separated list of branches to show data
        for.  If not provided, return data for all branches.
    days_ago: required.  Number of days ago for the "start" of the range.
    numdays: optional.  Number of days since days_ago.  Will default to
        "all since days ago"

    """
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
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_ref_data(request, project, table):
    """Get simple list of ref_data for ``table`` in ``project``"""
    stats = perftest_stats.get_ref_data(project, table)
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_range(request):
    """Utility function to extract the date range from the request."""
    days_ago = int(request.GET.get("days_ago"))
    numdays = int(request.GET.get("numdays", 0))

    return utils.get_day_range(days_ago, numdays)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = pushlog_stats.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), mimetype=APP_JS)
