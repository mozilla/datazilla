import json
from django.http import HttpResponse
from datazilla.controller.admin.stats import objectstore_stats
from .view_utils import get_range, REQUIRE_DAYS_AGO, APP_JS


def get_error_list(request, project):
    """
    Return a list of errors for a project
    """
    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)

    date_range = get_range(request)
    stats = objectstore_stats.get_error_list(
        project,
        date_range["start"],
        date_range["stop"],
        )
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_error_count(request, project):
    """Return a count of all objectstore entries with error"""

    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)

    date_range = get_range(request)
    stats = objectstore_stats.get_error_count(
        project,
        date_range["start"],
        date_range["stop"],
        )
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_json_blob(request, project, id):
    """Return a count of all objectstore entries with error"""

    blob = objectstore_stats.get_json_blob(project, id)
    return HttpResponse(blob, mimetype=APP_JS)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = objectstore_stats.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), mimetype=APP_JS)
