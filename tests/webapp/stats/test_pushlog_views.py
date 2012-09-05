from datazilla.controller.admin.stats import pushlog_stats
from tests.sample_data import create_date_based_data
from ...utils import jstr
from datazilla.model import utils
from datazilla.webapp.apps.datazilla.stats import view_utils

def test_get_not_referenced(ptm, client, monkeypatch):
    """
    Test that get_not_referenced uses the right dates without branches
    """
    def mock_get_not_referenced(project, startdate, enddate, branches):
        return {
            "project": project,
            "startdate": startdate,
            "enddate": enddate,
            "branches": branches,
            }
    monkeypatch.setattr(
        pushlog_stats,
        'get_not_referenced',
        mock_get_not_referenced,
        )

    date_range = utils.get_day_range(6)

    url = ("/{0}/stats/pushlog/not_referenced/?"
        "days_ago=6").format(ptm.project)
    response = client.get(url)

    exp = {
        "project": ptm.project,
        "startdate": date_range["start"],
        "enddate": date_range["stop"],
        "branches": None,
        }
    assert response.json == exp


def test_get_not_referenced_with_branches(ptm, client, monkeypatch):
    """
    Test that get_not_referenced uses the right dates and branches
    """
    def mock_get_not_referenced(project, startdate, enddate, branches):
        return {
            "project": project,
            "startdate": startdate,
            "enddate": enddate,
            "branches": branches,
            }
    monkeypatch.setattr(
        pushlog_stats,
        'get_not_referenced',
        mock_get_not_referenced,
        )

    date_range = utils.get_day_range(6)

    url = ("/{0}/stats/pushlog/not_referenced/?"
           "days_ago=6&branches=foo,bar").format(ptm.project)
    response = client.get(url)

    exp = {
        "project": ptm.project,
        "startdate": date_range["start"],
        "enddate": date_range["stop"],
        "branches": ["foo", "bar"],
        }
    assert response.json == exp


def test_get_not_referenced_missing_days_ago_param(ptm, client):
    """
    Test that 400 is returned when no days_ago param is used
    """
    url = "/{0}/stats/pushlog/not_referenced/".format(ptm.project)
    response = client.get(url, status=400)

    assert response.text == view_utils.REQUIRE_DAYS_AGO


def test_get_branches(client, monkeypatch):
    """Simple passthrough test."""
    def mock_get_all_branches():
        return ["foo", "bar"]
    monkeypatch.setattr(pushlog_stats, 'get_all_branches', mock_get_all_branches)

    url = "/stats/pushlog/branches/"
    response = client.get(url)

    assert response.json == ["foo", "bar"]


def test_get_db_size(plsm, client, monkeypatch):
    """Get the database size from the objectstore."""
    def mock_plsm():
        return plsm
    monkeypatch.setattr(pushlog_stats, 'get_plsm', mock_plsm)

    response = client.get("/stats/pushlog/db_size/")

    assert response.json == [
            {"size_mb": "0.13", "db_name": "{0}_hgmozilla_1".format(plsm.project)},
            ]
