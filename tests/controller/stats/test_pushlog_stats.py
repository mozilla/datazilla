from decimal import Decimal
import json

from datazilla.controller.admin.refdata import pushlog_refdata
from datazilla.model import factory

from ...sample_pushlog import get_pushlog_dict_set
from ...sample_data import perftest_data, testrun, perftest_json


def get_branch_id(plm, branch_name="Firefox"):
    """Use the Firefox branch as our common test branch"""
    branch = plm.get_branch_list(branch_name)
    return branch[0]["id"]


def test_get_not_referenced(plm, plsm, ptm, monkeypatch):
    """
    Test for runs that have matching revisions in the pushlogs.

    First one has a match, the other two don't
    """

    def mock_plsm():
        return plsm
    monkeypatch.setattr(factory, 'get_plsm', mock_plsm)

    def mock_plm():
        return plm
    monkeypatch.setattr(factory, 'get_plm', mock_plm)

    data1 = get_pushlog_dict_set()
    plm._insert_branch_pushlogs(
        get_branch_id(plm),
        data1,
        )

    blob = json.dumps(perftest_data())
    ptm.store_test_data(blob)
    ptm.process_objects(1)

    result = pushlog_refdata.get_not_referenced(
        ptm.project,
        startdate=1341451080,
        enddate=1341494822,
        )

    exp_matching = [{
        "push_id": 23046,
        "revisions": [
            "785345035a3b"
            ]}]

    exp_non_matching = [
        {
            "push_id": 23049,
            "revisions": [
                "fbd96a0bcc00",
                "fe305819d2f2"
            ]},
        {
            "push_id": 23052,
            "revisions": [
                "ea890a6eed56",
                "bd74a2949929",
                "5d6c06259bb1",
                "7209f9f14a7d"
            ]},
        ]

    assert result["with_matching_test_run"]["Firefox"]["pushlogs"] == exp_matching
    assert result["without_matching_test_run"]["Firefox"]["pushlogs"] == exp_non_matching


def test_get_pushlogs(plm, plsm, monkeypatch):
    """Test the get_pushlogs method."""

    def mock_plsm():
        return plsm
    monkeypatch.setattr(factory, 'get_plsm', mock_plsm)

    def mock_plm():
        return plm
    monkeypatch.setattr(factory, 'get_plm', mock_plm)

    data1 = get_pushlog_dict_set()
    plm._insert_branch_pushlogs(
        get_branch_id(plm),
        data1,
        )

    result = pushlog_refdata.get_pushlogs(
        startdate=1341451080,
        enddate=1341494822,
        )

    exp = {
        23049: {
            "branch_name": "Firefox",
            "revisions": [
                "fbd96a0bcc00",
                "fe305819d2f2"
            ]
        },
        23052: {
            "branch_name": "Firefox",
            "revisions": [
                "ea890a6eed56",
                "bd74a2949929",
                "5d6c06259bb1",
                "7209f9f14a7d"
            ]
        },
        23046: {
            "branch_name": "Firefox",
            "revisions": [
                "785345035a3b"
            ]
        }
    }


    assert result == exp



def test_get_all_branches(plm, monkeypatch):
    """Test get_all_branches method."""

    def mock_plm():
        return plm
    monkeypatch.setattr(factory, 'get_plm', mock_plm)

    exp_branch_list = [
        u"Firefox",
        u"Try",
        u"Mozilla-Aurora",
        u"Mozilla-Beta",
        u"Mozilla-Release",
        u"Mozilla-Esr10",
        u"Accessibility",
        u"Addon-SDK",
        u"Build-System",
        u"Devtools",
        u"Fx-Team",
        u"Ionmonkey",
        u"J\xe4gerMonkey",
        u"Profiling",
        u"Services-Central",
        u"UX",
        u"Alder",
        u"Ash",
        u"Birch",
        u"Cedar",
        u"Elm",
        u"Holly",
        u"Larch",
        u"Maple",
        u"Oak",
        u"Pine",
        u"Electrolysis",
        u"Graphics",
        u"Places",
        u"Mozilla-Inbound"
    ]

    assert set(exp_branch_list) == set(pushlog_refdata.get_all_branches())


def test_get_db_size(plsm, monkeypatch):
    """Test the get_db_size method."""
    def mock_plsm():
        return plsm
    monkeypatch.setattr(factory, 'get_plsm', mock_plsm)

    size = pushlog_refdata.get_db_size()

    assert size[0]["db_name"] == u'{0}_hgmozilla_1'.format(plsm.project)
    assert size[0]["size_mb"] > 0
