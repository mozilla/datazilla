import json
import re
from django.http import HttpResponse
from datazilla.controller.admin.refdata import objectstore_refdata
from .view_utils import get_range, REQUIRE_DAYS_AGO, API_CONTENT_TYPE


def get_error_list(request, project):
    """Return a list of errors for a project."""
    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)

    date_range = get_range(request)
    stats = objectstore_refdata.get_error_list(
        project,
        date_range["start"],
        date_range["stop"],
        )
    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_error_count(request, project):
    """Return a count of all objectstore entries with error"""

    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)

    date_range = get_range(request)
    stats = objectstore_refdata.get_error_count(
        project,
        date_range["start"],
        date_range["stop"],
        )
    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_json_blob(request, project, id):
    """Return a count of all objectstore entries with error"""

    blob = objectstore_refdata.get_json_blob(project, id)

    if blob:

        # If we don't have malformed json load it so we can return
        # a single json data structure with all fields present including
        # json_blob.  Malformed json will be returned as an escaped
        # string.
        try:
            blob['json_blob'] = json.loads(blob['json_blob'])
        except ValueError as e:
            pass

        return HttpResponse(json.dumps(blob), content_type=API_CONTENT_TYPE)

    else:
        return HttpResponse("Id not found: {0}".format(id), status=404)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = objectstore_refdata.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), content_type=API_CONTENT_TYPE)
