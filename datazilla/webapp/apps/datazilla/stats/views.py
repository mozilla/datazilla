import json
from django.http import HttpResponse

from datazilla.controller.admin.stats import objectstore_stats
from datazilla.model import utils
from datazilla.webapp.apps.datazilla.views import APP_JS

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
    json_stats = json.dumps(stats)
    return HttpResponse(json.dumps(json_stats), mimetype=APP_JS)


def get_count_errors(request, project):
    """Return a count of all objectstore entries with error"""

    range = utils.get_day_range(5)
    stats = objectstore_stats.get_count_errors(
        project,
        )
    json_stats = json.dumps(stats)
    return HttpResponse(json.dumps({"camsays": "success"}), mimetype=APP_JS)
