import json

from django.http import HttpResponse

from datazilla.controller.admin.stats import perftest_stats
from datazilla.model import utils

APP_JS = 'application/json'

def get_runs_by_branch(request, project):
    """
    Return the testruns for a project broken down by branches.

    days_ago: required.  Number of days ago for the "start" of the range.
    numdays: optional.  Number of days since days_ago.  Will default to
        "all since days ago"

    """
    if not request.GET.get("days_ago"):
        return HttpResponse("Invalid Request: Require days_ago parameter. "
        "This specifies the number of days ago to use as the start date range for this response.", status=400)
    range = _get_range(request)
    stats = perftest_stats.get_runs_by_branch(
        project,
        range["start"],
        range["stop"],
        )
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_ref_data(request, project, table):
    """Get simple list of ref_data for ``table`` in ``project``"""
    stats = perftest_stats.get_ref_data(project, table)
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = perftest_stats.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), mimetype=APP_JS)


def _get_range(request):
    """Utility function to extract the date range from the request."""
    days_ago = int(request.GET.get("days_ago"))
    numdays = int(request.GET.get("numdays", 0))

    return utils.get_day_range(days_ago, numdays)
