from datazilla.controller.admin.refdata import perftest_refdata
from tests.sample_data import create_date_based_data
from datazilla.model import utils, factory
from datazilla.webapp.apps.datazilla.refdata import view_utils

def test_get_runs_by_branch_show_test_runs_true(ptm, plm, client, monkeypatch):
    """
    Test that with show_runs=True that you get the runs and counts
    """
    def mock_plm():
        return plm
    monkeypatch.setattr(factory, 'get_plm', mock_plm)

    dates = [
        utils.get_day_range(5)["start"],
        utils.get_day_range(4)["start"],
        utils.get_day_range(3)["start"],
        ]
    create_date_based_data(ptm, monkeypatch, dates)
    url = "/{0}/refdata/perftest/runs_by_branch/?show_test_runs=True&days_ago=6".format(ptm.project)
    response = client.get(url)

    exp = set(["count", "limit", "total_count", "test_runs"])
    assert set(response.json["Mozilla-Aurora"].keys()) == exp


def test_get_runs_by_branch_show_test_runs_false(ptm, client, monkeypatch):
    """
    Test that with show_runs not present that you get the counts only
    """
    dates = [
        utils.get_day_range(5)["start"],
        utils.get_day_range(4)["start"],
        utils.get_day_range(3)["start"],
        ]
    create_date_based_data(ptm, monkeypatch, dates)
    url = "/{0}/refdata/perftest/runs_by_branch/?days_ago=6".format(ptm.project)
    response = client.get(url)

    exp = ["count"]
    assert response.json["Mozilla-Aurora"].keys() == exp


def test_get_runs_by_branch_missing_days_ago_param(ptm, client):
    """
    Test that 400 is returned when no days_ago param is used
    """
    url = "/{0}/refdata/perftest/runs_by_branch/".format(ptm.project)
    response = client.get(url, status=400)

    assert response.text == view_utils.REQUIRE_DAYS_AGO


def test_get_ref_data(ptm, client, monkeypatch):
    """Test that we're hitting the right controller method"""
    def mock_get_ref_data(project, table):
        return {"result": "{0} - {1}".format(project, table)}
    monkeypatch.setattr(perftest_refdata, 'get_ref_data', mock_get_ref_data)

    url = "/{0}/refdata/perftest/ref_data/machines/".format(ptm.project)
    response = client.get(url)

    assert response.json == {"result": "{0} - {1}".format(
        ptm.project,
        "machines",
        )}


def test_get_db_size(ptm, client):
    """Get the database size from the objectstore."""
    response = client.get("/{0}/refdata/perftest/db_size/".format(ptm.project))

    db_names = set([
        "{0}_objectstore_1".format(ptm.project),
        "{0}_perftest_1".format(ptm.project)]
        )

    for d in response.json:
        assert d['db_name'] in db_names

        size_mb = float(d['size_mb'])
        assert size_mb > 0
