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

REQUIRE_BRANCH_NAME = """Invalid Request: Require branch parameter.
                     This specifies the name of the branch to retrieve data
                     for (Mozilla-Inbound, Mozilla-Release etc...)"""

REQUIRE_OS_OR_TEST_NAME = """Invalid Request: Require os and os_version or test_name parameter. All of these parameters may also be defined Examples: os=mac, os_version=OS X 10.8  or test_name=a11yr."""

REQUIRE_TEST_NAME = """Invalid Request: Require test_name parameter.
                     This specifies the name of the test."""

REQUIRE_PAGE_NAME = """Invalid Request: Require page_name parameter.
                     This specifies the name of the test page."""

API_CONTENT_TYPE = 'application/json; charset=utf-8'

DEFAULT_BRANCH_PROJECT_MAP = {
    'talos':{'branch':'Mozilla-Inbound', 'product':'Firefox' },
    'b2g':{'branch':'master', 'product':'B2G'},
    'stoneridge':{'branch':'broadband', 'product':'Firefox'},
    'test':{'branch':'Mozilla-Inbound-Non-PGO', 'product':'Firefox'},
    'default':{'branch':'Mozilla-Inbound', 'product':'Firefox'},
}

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
    device = request.GET.get("device", "unagi")

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
            project, branch, device, test_ids, page_name, begin, now
            )),
        content_type=API_CONTENT_TYPE,
        )

def get_data_all_dimensions(request, project=""):

    product = request.GET.get('product')

    branch = request.GET.get('branch')

    os = request.GET.get('os')

    os_version = request.GET.get('os_version')

    test = request.GET.get('test')

    page = request.GET.get('page')

    start_time = request.GET.get('start')

    end_time = request.GET.get('stop')

    if not product:
        return HttpResponse(REQUIRE_PRODUCT_NAME, status=400)

    if not branch:
        return HttpResponse(REQUIRE_BRANCH_NAME, status=400)

    if (not os) and (not os_version) and (not test):
        #Require at least os
        return HttpResponse(REQUIRE_OS_OR_TEST_NAME, status=400)

    data = testdata.get_test_data_all_dimensions(
        project, product, branch, os, os_version, test, page,
        start_time, end_time)

    return HttpResponse(
        json.dumps(data), content_type=API_CONTENT_TYPE)

def get_platforms_and_tests(request, project=""):

    start_time = request.GET.get('start')

    end_time = request.GET.get('stop')

    product = request.GET.get('product')

    branch = request.GET.get('branch')

    if not branch:
        if project in DEFAULT_BRANCH_PROJECT_MAP:
            branch = DEFAULT_BRANCH_PROJECT_MAP[project]['branch']
        else:
            branch = DEFAULT_BRANCH_PROJECT_MAP['default']['branch']

    if not product:
        if project in DEFAULT_BRANCH_PROJECT_MAP:
            product = DEFAULT_BRANCH_PROJECT_MAP[project]['product']
        else:
            product = DEFAULT_BRANCH_PROJECT_MAP['default']['product']

    data = testdata.get_platforms_and_tests(
        project, product, branch, start_time, end_time)

    return HttpResponse(
        json.dumps(data), content_type=API_CONTENT_TYPE)

def get_all_data_date_range(request, project=""):

    data = testdata.get_all_dimension_data_range(project)

    return HttpResponse(
        json.dumps(data), content_type=API_CONTENT_TYPE)


