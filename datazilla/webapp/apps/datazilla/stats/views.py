import json
from django.http import HttpResponse

from datazilla.controller.admin.stats import objectstore_stats
from datazilla.model import utils

APP_JS = 'application/json'

def get_list_errors(request, project):
    """
    Return a list of errors for a project
    """
    range = utils.get_day_range(5)
    stats = objectstore_stats.get_list_errors(
        project,
        range["start"],
        range["stop"],
        )
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_count_errors(request, project):
    """Return a count of all objectstore entries with error"""

    range = utils.get_day_range(5)
    stats = objectstore_stats.get_count_errors(
        project,
        )
    return HttpResponse(json.dumps(stats), mimetype=APP_JS)


def get_json_blob(request, project, id):
    """Return a count of all objectstore entries with error"""

    blob = objectstore_stats.get_json_blob(project, id)
    return HttpResponse(blob, mimetype=APP_JS)
