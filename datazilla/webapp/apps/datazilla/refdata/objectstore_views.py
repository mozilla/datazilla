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

def get_json_blob_by_revisions(request, project):

    branch = request.GET.get("branch")
    gaia_revision = request.GET.get("gaia_revision")
    gecko_revision = request.GET.get("gecko_revision")
    test_id = request.GET.get("test_id")
    test_type = request.GET.get("test_type")

    bad_param = False
    try:
        test_id = int(test_id)
    except ValueError:
        bad_param = True

    blobs = objectstore_refdata.get_json_blob_by_revisions(
        project, branch, gaia_revision, gecko_revision, test_id, test_type)

    if blobs and not bad_param:
        try:
            for index, b in enumerate(blobs):
                blobs[index]['json_blob'] = json.loads(b['json_blob'])
        except ValueError as e:
            pass

        return HttpResponse(json.dumps(blobs), content_type=API_CONTENT_TYPE)
    else:
        return HttpResponse(
            "gaia revision, {0}, and gecko revision, {1}, test {2} not found".format(gaia_revision, gecko_revision, str(test_id)),
            status=404)

def get_json_blob(request, project, id):
    """Return a json object for the objectstore id provided"""

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

def get_json_blob_by_test_run_id(request, project, test_run_id):
    """Return a json object for the test_run_id provided"""

    blob = objectstore_refdata.get_json_blob_by_test_run_id(
        project, test_run_id)

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
