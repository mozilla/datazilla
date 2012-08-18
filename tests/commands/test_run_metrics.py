"""
Tests for management command to create perftest database.

"""
import pytest

from django.core.management import call_command

from ..model.test_metrics_test_model import setup_pushlog_walk_tests

def call_run_metrics(*args, **kwargs):
    call_command("run_metrics", *args, **kwargs)

def test_no_numdays(capsys):

    call_run_metrics(project="talos")

    exp = (
        "You must supply the number of days data.\n",
        "",
        )

    assert capsys.readouterr() == exp

def test_bad_numdays(capsys):

    call_run_metrics(numdays="numdays")

    exp = (
        "numdays must be an integer.\n",
        "",
        )

    assert capsys.readouterr() == exp

def test_no_args(capsys):
    with pytest.raises(SystemExit):
        call_run_metrics()

    exp = (
        "",
        "Error: You must supply a project name: --project project\n",
        )

    assert capsys.readouterr() == exp

def test_find_parent_case_one(mtm, ptm, plm, monkeypatch):

    setup_data = setup_pushlog_walk_tests(mtm, ptm, plm, monkeypatch)

    print setup_data


