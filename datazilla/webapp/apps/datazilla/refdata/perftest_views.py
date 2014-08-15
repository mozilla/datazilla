import json
import urllib2

from django.http import HttpResponse

from datazilla.controller.admin.refdata import perftest_refdata
from .view_utils import get_range, REQUIRE_DAYS_AGO, API_CONTENT_TYPE


def get_runs_by_branch(request, project):
    """
    Return the testruns for a project broken down by branches.

    days_ago: required.  Number of days ago for the "start" of the range.
    numdays: optional.  Number of days since days_ago.  Will default to
        "all since days ago"

    """
    if not request.GET.get("days_ago"):
        return HttpResponse(REQUIRE_DAYS_AGO, status=400)

    range = get_range(request)

    show_tr = request.GET.get("show_test_runs")
    if show_tr and show_tr.lower() == "true":
        stats = perftest_refdata.get_runs_by_branch(
            project,
            range["start"],
            range["stop"],
            )
    else:
        stats = perftest_refdata.get_run_counts_by_branch(
            project,
            range["start"],
            range["stop"],
            )

    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_ref_data(request, project, table):
    """Get simple list of ref_data for ``table`` in ``project``"""
    stats = perftest_refdata.get_ref_data(project, table)
    return HttpResponse(json.dumps(stats), content_type=API_CONTENT_TYPE)


def get_db_size(request, project):
    """Return the size of the DB on disk in MB."""
    size_tuple = perftest_refdata.get_db_size(project)
    #JSON can't serialize a decimal, so converting size_MB to string
    result = []
    for item in size_tuple:
        item["size_mb"] = str(item["size_mb"])
        result.append(item)
    return HttpResponse(json.dumps(result), content_type=API_CONTENT_TYPE)

def get_b2g_targets(request, project):

    url = 'https://raw.githubusercontent.com/mozilla-b2g/gaia/master/tests/performance/config.json'

    response = {}
    response['url'] = url

    try:
        resp = urllib2.urlopen(url, timeout=5)
    except urllib2.URLError, e:
        response['msg'] = "Failed to retrieve the url"
    else:
        data = json.loads(resp.read())
        response['data'] = data.get('goals', 'goals key not found in http response data')
        response['code'] = resp.getcode()
        response['msg'] = resp.msg

    return HttpResponse(json.dumps(response), content_type=API_CONTENT_TYPE)

