import json

from django.http import HttpResponse

from datazilla.controller.admin import testdata

API_CONTENT_TYPE = 'application/json; charset=utf-8'

def get_testdata(request, project, branch, revision):
    """

    """
    os_name = request.GET.get("os_name", None)
    test_name = request.GET.get("test_name", None)

    return HttpResponse(
        json.dumps(testdata.get_testdata(
            project,
            branch,
            revision,
            os_name=os_name,
            test_name=test_name,
            )),
        content_type=API_CONTENT_TYPE,
        )


def get__metricsdata(request, project, branch, revision):
    """

    """
    os_name = request.GET.get("os_name", None)
    test_name = request.GET.get("test_name", None)

    return HttpResponse(
        json.dumps(testdata.get_metrics_data(
            project,
            branch,
            revision,
            os_name=os_name,
            test_name=test_name,
            )),
        content_type=API_CONTENT_TYPE,
        )
