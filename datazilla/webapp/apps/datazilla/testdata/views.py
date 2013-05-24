import json
import time

from django.http import HttpResponse

from datazilla.controller.admin import testdata
from datazilla.model import utils

REQUIRE_DAYS_AGO = """Invalid Request: Require days_ago parameter.
                    This specifies the number of days ago to use as the start
                    date range for this response."""

REQUIRE_PRODUCT_NAME = """Invalid Request: Require product parameter.
                     This specifies the name of the product to retrieve data
                     for (Firefox, Fennec etc...)"""

REQUIRE_TEST_NAME = """Invalid Request: Require test_name parameter.
                     This specifies the name of the test."""

REQUIRE_PAGE_NAME = """Invalid Request: Require page_name parameter.
                     This specifies the name of the test page."""

API_CONTENT_TYPE = 'application/json; charset=utf-8'

def get_testdata(request, project, branch, revision):
    """
    Apply data filters and return all test data objects associated with the
    revision.
    """
    product_name = request.GET.get("product", None)
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
            product_name=product_name,
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

    #Default to most current version of Firefox
    product_name = request.GET.get("product", "Firefox")
    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)

    branch_version = request.GET.get("branch_version", None)
    if not branch_version:
        branch_version = testdata.get_default_version(
            project, branch, product_name
            )

    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)
    page_name = request.GET.get("page_name", None)

    return HttpResponse(
        json.dumps(testdata.get_metrics_data(
            project,
            branch,
            revision,
            product_name=product_name,
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

    #Default to most current version of Firefox
    product_name = request.GET.get("product", "Firefox")
    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)

    branch_version = request.GET.get("branch_version", None)
    if not branch_version:
        branch_version = testdata.get_default_version(
            project, branch, product_name
            )

    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)
    pushlog_project = request.GET.get("pushlog_project", None)

    return HttpResponse(
        json.dumps(testdata.get_metrics_summary(
            project,
            branch,
            revision,
            product_name=product_name,
            os_name=os_name,
            os_version=os_version,
            branch_version=branch_version,
            processor=processor,
            build_type=build_type,
            test_name=test_name,
            pushlog_project=pushlog_project
            )),
        content_type=API_CONTENT_TYPE,
        )

def get_metrics_pushlog(request, project, branch, revision):
    """
    Apply filters and return trend line data for the time period requested.
    """

    #Default to most current version of Firefox
    product_name = request.GET.get("product", "Firefox")
    os_name = request.GET.get("os_name", None)
    os_version = request.GET.get("os_version", None)

    branch_version = request.GET.get("branch_version", None)
    if not branch_version:
        branch_version = testdata.get_default_version(
            project, branch, product_name
            )

    processor = request.GET.get("processor", None)
    build_type = request.GET.get("build_type", None)
    test_name = request.GET.get("test_name", None)
    page_name = request.GET.get("page_name", None)

    #applies to both before/after, so total of 2*maximum_pushes
    #are allowed
    maximum_pushes = 1000

    #cast pushes_before/pushes_after to an int to scrub user
    #supplied data
    pushes_before =5
    try:
        pushes_before = int(request.GET.get("pushes_before", pushes_before))
    except ValueError:
        pass

    pushes_after = 5
    try:
        pushes_after = int(request.GET.get("pushes_after", pushes_after))
    except ValueError:
        pass

    #Set maximum limit for pushes before/after
    if pushes_before > maximum_pushes:
        pushes_before = maximum_pushes
    if pushes_after > maximum_pushes:
        pushes_after = maximum_pushes

    pushlog_project = request.GET.get("pushlog_project", None)

    if not test_name:
        return HttpResponse(REQUIRE_TEST_NAME, status=400)

    if not page_name:
        return HttpResponse(REQUIRE_PAGE_NAME, status=400)

    return HttpResponse(
        json.dumps(testdata.get_metrics_pushlog(
            project,
            branch,
            revision,
            product_name=product_name,
            os_name=os_name,
            os_version=os_version,
            branch_version=branch_version,
            processor=processor,
            build_type=build_type,
            test_name=test_name,
            page_name=page_name,
            pushes_before=pushes_before,
            pushes_after=pushes_after,
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

def get_test_value_summary(request, project):

    branch = request.GET['branch']
    test_ids = utils.get_id_list(request.GET['test_ids'])
    page_name = request.GET.get("page_name", "")
    range = request.GET.get("range", 7)

    #make sure we're operating on an int
    try:
        range = int(range)
    except ValueError:
        range = 7

    now = int(time.time())

    begin = now - 604800

    if range == 30:
        begin = now - 2592000
    if range == 60:
        begin = now - 5184000
    elif range == 90:
        begin = now - 7776000

    return HttpResponse(
        json.dumps(testdata.get_test_value_summary(
            project, branch, test_ids, page_name, begin, now
            )),
        content_type=API_CONTENT_TYPE,
        )

def get_data_all_dimensions(request, project=""):

    #default: last 7 days
    start_time = request.GET.get('start')
    #default: now
    end_time = request.GET.get('stop')

    data = testdata.get_test_data_all_dimensions(
        project, start_time, end_time)

    return HttpResponse(
        json.dumps(data), content_type=API_CONTENT_TYPE)




