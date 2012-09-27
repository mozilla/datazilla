import json

from django.http import HttpResponse

from datazilla.controller.admin import testdata

REQUIRE_DAYS_AGO = """Invalid Request: Require days_ago parameter.
                    This specifies the number of days ago to use as the start
                    date range for this response."""

REQUIRE_TEST_NAME = """Invalid Request: Require test_name parameter.
                     This specifies the name of the test."""

API_CONTENT_TYPE = 'application/json; charset=utf-8'


def get_testdata(request, project, branch, revision):
    """
    Apply data filters and return all test data objects associated with the
    revision.
    """
    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)
    branch_version = request.GET.get("branch_version", None)
    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)
    page_name = request.GET.get("page_name", None)

    return HttpResponse(
        json.dumps(testdata.get_testdata(
            project,
            branch,
            revision,
            os_name=os_name,
            os_version=os_version,
            branch_version=branch_version,
            processor=processor,
            build_type=build_type,
            test_name=test_name,
            page_name=page_name,
            )),
        content_type=API_CONTENT_TYPE,
        )


def get_metrics_data(request, project, branch, revision):
    """
    Apply filters and return all metrics data associated with the revision.
    """
    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)
    branch_version = request.GET.get("branch_version", None)
    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)
    page_name = request.GET.get("page_name", None)

    return HttpResponse(
        json.dumps(testdata.get_metrics_data(
            project,
            branch,
            revision,
            os_name=os_name,
            os_version=os_version,
            branch_version=branch_version,
            processor=processor,
            build_type=build_type,
            test_name=test_name,
            page_name=page_name,
            )),
        content_type=API_CONTENT_TYPE,
        )

def get_metrics_summary(request, project, branch, revision):
    """
    Apply filters and build a summary of all metric test evaluations.
    """

    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)
    branch_version = request.GET.get("branch_version", None)
    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)

    return HttpResponse(
        json.dumps(testdata.get_metrics_summary(
            project,
            branch,
            revision,
            os_name=os_name,
            os_version=os_version,
            branch_version=branch_version,
            processor=processor,
            build_type=build_type,
            test_name=test_name,
            )),
        content_type=API_CONTENT_TYPE,
        )

def get_metrics_pushlog(request, project, branch):
    """
    Apply filters and return trend line data for the time period requested.
    """
    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)
    branch_version = request.GET.get("branch_version", None)
    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)
    page_name = request.GET.get("page_name", None)
    days_ago = request.GET.get("days_ago", None)
    numdays = request.GET.get("numdays", None)

    pushlog_project = request.GET.get("pushlog_project", None)

    if not days_ago:
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)
    if not test_name:
        return HttpResponse(REQUIRE_TEST_NAME, status=400)

    return HttpResponse(
        json.dumps(testdata.get_metrics_pushlog(
            project,
            branch,
            os_name=os_name,
            os_version=os_version,
            branch_version=branch_version,
            processor=processor,
            build_type=build_type,
            test_name=test_name,
            page_name=page_name,
            days_ago=days_ago,
            numdays=numdays,
            pushlog_project=pushlog_project
            )),
        content_type=API_CONTENT_TYPE,
        )

def get_application_log(request, project, revision):
    """
    Retrieve all application log entries for this revision.
    """
    return HttpResponse(
        json.dumps(testdata.get_application_log(
            project,
            revision
            )),
        content_type=API_CONTENT_TYPE,
        )


