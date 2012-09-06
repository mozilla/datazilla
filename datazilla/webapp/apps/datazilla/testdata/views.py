import json

from django.http import HttpResponse

from datazilla.controller.admin.stats import pushlog_stats

API_CONTENT_TYPE = 'application/json; charset=utf-8'

def get_testdata(request, project, branch, revision):
    """

    """
    return HttpResponse(
        json.dumps({"stuff":[project, branch, revision]}),
        content_type=API_CONTENT_TYPE,
        )


