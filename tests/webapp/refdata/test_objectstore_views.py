from tests.sample_data import create_date_based_data
from ...utils import jstr
from datazilla.model import utils
from datazilla.webapp.apps.datazilla.refdata import view_utils


def test_get_error_list(ptm, client, monkeypatch):
    """Get a list of errors from the objectstore in a date range."""

    dates = [
        utils.get_day_range(5)["start"],
        utils.get_day_range(4)["start"],
        utils.get_day_range(3)["start"],
        ]
    create_date_based_data(ptm, monkeypatch, dates)
    url = "/{0}/refdata/objectstore/error_list/?days_ago=4".format(ptm.project)
    response = client.get(url)

    exp = [{
            u"date_loaded": dates[2],
            u"id": 2,
            u"test_run_id": None,
            u"worker_id": None,
            u"processed_flag": u"ready",
            u"error_msg": u"Malformed JSON"
            }]
    assert response.json == exp


def test_get_error_list_no_days_ago(ptm, client):
    """Get a 400 when omitting required param of days_ago."""

    url = "/{0}/refdata/objectstore/error_list/".format(ptm.project)
    response = client.get(url, status=400)
    assert response.text == view_utils.REQUIRE_DAYS_AGO


def test_get_error_count(ptm, client, monkeypatch):
    """Get a count of errors from the objectstore in a date range."""

    dates = [
        utils.get_day_range(5)["start"],
        utils.get_day_range(4)["start"],
        utils.get_day_range(3)["start"],
        ]
    create_date_based_data(ptm, monkeypatch, dates)
    url = "/{0}/refdata/objectstore/error_count/?days_ago=6".format(ptm.project)
    response = client.get(url)

    exp = [
        {
            "count": 1,
            "message": "Malformed JSON"
            },
        {
            "count": 1,
            "message": "Other"
            }]

    assert response.json == exp


def test_get_error_count_no_days_ago(ptm, client):
    """Get a 400 when omitting required param of days_ago."""

    url = "/{0}/refdata/objectstore/error_count/".format(ptm.project)
    response = client.get(url, status=400)
    assert response.text == view_utils.REQUIRE_DAYS_AGO


def test_get_json_blob(ptm, client, monkeypatch):
    """Fetch JSON for an ID that has good JSON."""
    dates = [
        utils.get_day_range(5)["start"],
        utils.get_day_range(4)["start"],
        utils.get_day_range(3)["start"],
        ]
    create_date_based_data(ptm, monkeypatch, dates)
    url = "/{0}/refdata/objectstore/json_blob/3/".format(ptm.project)
    response = client.get(url)

    exp_tm = {
        u"platform": u"x86_64",
        u"osversion": u"Ubuntu 11.10",
        u"os": u"linux",
        u"name": u"qm-pxp01"
        }

    exp_tb = {
        u"version": u"14.0a2",
        u"revision": u"785345035a3b",
        u"name": u"one",
        u"branch": u"Mozilla-Aurora",
        }
    exp_tr = {
        u"date": dates[1],
        u"suite": u"Talos tp5r",
        u"options": {
            u"responsiveness": u"false",
            u"tpmozafterpaint": u"false",
            u"tpdelay": u"",
            u"tpchrome": u"true",
            u"tppagecycles": u"1",
            u"tpcycles": u"3",
            u"tprender": u"false",
            u"shutdown": u"true",
            u"rss": u"true"
        }}
    exp_ra = {
        u"three.com": [
            789.0,
            705.0,
            739.0
        ],
        u"one.com": [
            789.0,
            705.0,
            739.0
        ],
        u"two.com": [
            789.0,
            705.0,
            739.0
        ]}
    exp_res = {
        u"three.com": [
            789.0,
            705.0,
            739.0
        ],
        u"one.com": [
            789.0,
            705.0,
            739.0
        ],
        u"two.com": [
            789.0,
            705.0,
            739.0
        ]}

    rj = response.json

    assert rj["test_machine"] == exp_tm

    # these ids can vary
    del(rj["test_build"]["id"])

    assert rj["test_build"] == exp_tb
    assert rj["testrun"] == exp_tr
    assert rj["results_aux"] == exp_ra
    assert rj["results"] == exp_res


def test_get_json_blob_bad_id(ptm, client, monkeypatch):
    """Attempt to fetch the JSON for an ID that doesn't exist."""
    create_date_based_data(ptm, monkeypatch)
    url = "/{0}/refdata/objectstore/json_blob/22/".format(ptm.project)
    response = client.get(url, status=404)

    exp = "Id not found: 22"

    assert response.text == exp


def test_get_db_size(ptm, client):
    """Get the database size from the objectstore."""
    response = client.get("/{0}/refdata/objectstore/db_size/".format(ptm.project))

    db_names = set(
        ["{0}_objectstore_1".format(ptm.project),
         "{0}_perftest_1".format(ptm.project) ]
        )

    for data in response.json:

       assert data['db_name'] in db_names

       size_mb = float(data['size_mb'])

       assert size_mb > 0
