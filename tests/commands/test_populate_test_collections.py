"""
Tests for management command to populate test collections.

"""

from django.core.management import call_command
from datazilla.controller.admin import collection



def call_populate_test_collections(*args, **kwargs):
    call_command("populate_test_collections", *args, **kwargs)


def test_no_args(capsys):
    """Shows need for a project name."""
    try:
        call_populate_test_collections()
        raise Exception("Should have gotten a SystemExit")

    except SystemExit:
        exp = (
            "",
            "Error: You must supply a project name to create: --project project\n",
            )

        assert capsys.readouterr() == exp


def test_successful_populate(monkeypatch):
    """Successful populate_test_collections."""

    calls = []
    def mock_load(project):
        calls.append(project)
    monkeypatch.setattr(collection, "load_test_collection", mock_load)

    call_populate_test_collections(
        project="spam",
        load=True,
        )

    assert set(calls) == set(["spam"])


def test_no_load(monkeypatch):
    """Successful populate_test_collections."""

    calls = []
    def mock_load(project):
        calls.append(project)
    monkeypatch.setattr(collection, "load_test_collection", mock_load)

    call_populate_test_collections(
        project="spam",
        )

    assert set(calls) == set([])
