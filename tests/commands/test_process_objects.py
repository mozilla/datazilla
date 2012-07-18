"""
Tests for management command to process objects.

"""

from django.core.management import call_command
from datazilla.model import PerformanceTestModel



def call_process_objects(*args, **kwargs):
    call_command("process_objects", *args, **kwargs)


def test_no_args(capsys):
    """Shows need for a project name."""
    try:
        call_process_objects()
        raise Exception("Should have gotten a SystemExit")

    except SystemExit:
        exp = (
            "",
            "Error: You must provide either a project or cron_batch value.\n",
            )

        assert capsys.readouterr() == exp


def test_successful_populate(monkeypatch):
    """Successful populate_test_collections."""

    calls = []
    def mock_process(justme, project):
        calls.append(project)
    monkeypatch.setattr(PerformanceTestModel, "process_objects", mock_process)

    call_process_objects(
        project="testproj",
        loadlimit=25,
        )

    assert set(calls) == set([25])


def test_no_load(monkeypatch):
    """Successful populate_test_collections."""

    calls = []
    def mock_process(justme, loadlimit):
        calls.append(loadlimit)
    monkeypatch.setattr(PerformanceTestModel, "process_objects", mock_process)

    call_process_objects(
        project="testproj",
    )

    assert set(calls) == set([1])
