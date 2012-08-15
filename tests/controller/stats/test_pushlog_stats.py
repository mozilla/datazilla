import json

from datazilla.model.base import TestDataError, TestData

from datazilla.controller.admin.stats import pushlog_stats

from ...sample_pushlog import get_pushlog_dict_set1
from ...sample_data import perftest_data, testrun


def get_branch_id(plm, branch_name="Firefox"):
    """Use the Firefox branch as our common test branch"""
    branch = plm.get_branch_list(branch_name)
    return branch[0]["id"]


def test_get_not_referenced(plsm, ptsm, monkeypatch):

    def mock_ptsm(project):
        return ptsm
    monkeypatch.setattr(pushlog_stats, 'ptsm', mock_ptsm)

    def mock_plsm():
        return plsm
    monkeypatch.setattr(pushlog_stats, 'plsm', mock_plsm)


    data1 = get_pushlog_dict_set1()
    plsm._insert_branch_pushlogs(
        get_branch_id(plsm),
        data1,
        )

    tr_revision = data1["23046"]["changesets"][0]["node"][:12]
    data = TestData(perftest_data(testrun=testrun(revision=tr_revision)))

    test_id = ptsm._get_or_create_test_id(data)
    os_id = ptsm._get_or_create_os_id(data)
    product_id = ptsm._get_or_create_product_id(data)
    machine_id = ptsm._get_or_create_machine_id(data, os_id)

    build_id = ptsm._set_build_data(data, product_id)

    test_run_id = ptsm._set_test_run_data(data, test_id, build_id, machine_id)

    result = pushlog_stats.get_not_referenced(
        ptsm.project,
        startdate=1341451081,
        enddate=1341494822,
        )
    assert result == "foo"


def test_get_all_branches(plsm, monkeypatch):

    def mock_plsm():
        return plsm
    monkeypatch.setattr(pushlog_stats, 'plsm', mock_plsm)

    exp_branch_list = [
        "Firefox",
        "Try",
        "Mozilla-Aurora",
        "Mozilla-Beta",
        "Mozilla-Release",
        "Mozilla-Esr10",
        "Accessibility",
        "Addon-SDK",
        "Build-System",
        "Devtools",
        "Fx-Team",
        "Ionmonkey",
        "JägerMonkey",
        "Profiling",
        "Services-Central",
        "UX",
        "Alder",
        "Ash",
        "Birch",
        "Cedar",
        "Elm",
        "Holly",
        "Larch",
        "Maple",
        "Oak",
        "Pine",
        "Electrolysis",
        "Graphics",
        "Places",
        "Mozilla-Inbound"
    ]

    assert set(exp_branch_list) == set(pushlog_stats.get_all_branches())

def test_get_db_size(plsm):
    size = plsm.get_db_size()

    assert size[0]["db_name"] == u'cam_testpushlog_hgmozilla_1'
    assert size[0]["size_mb"] > 0
