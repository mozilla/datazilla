"""
Tests for management command to populate the summary cache.

"""
import pytest

from django.core.management import call_command
from datazilla.controller.admin import summary
from datazilla.model.sql.models import DataSource



def call_populate_summary_cache(*args, **kwargs):
    call_command("populate_summary_cache", *args, **kwargs)


def create_project(name, cron_batch):
    """Create a dummy perftest project record"""
    DataSource.objects.create(
        project=name,
        cron_batch=cron_batch,
        dataset=1,
        type="MySQL-InnoDB",
        name="{0}_perftest_1".format(name),
        host="s4n4.qa.phx1.mozilla.com",
        contenttype="perftest",
        creation_date="2012-08-10 03:23",
        )


def test_no_args(capsys):
    """Shows need for a project or cron_batch."""
    with pytest.raises(SystemExit):
        call_populate_summary_cache()

    exp = (
        "",
        "Error: You must provide either a project or cron_batch value.\n",
        )

    assert capsys.readouterr() == exp


def test_build(capsys, monkeypatch, ptm):
    """Test that passing the build and project params calls the right summary method"""

    calls = []
    def mock_build(project):
        calls.append("mock build for {0}".format(project))
    monkeypatch.setattr(summary, "build_test_summaries", mock_build)

    call_populate_summary_cache(build=True, project=ptm.project)
    assert calls[0] == "mock build for {0}".format(ptm.project)

    exp = (
        u"Starting for projects: {0}\n".format(ptm.project) +
        u"Processing project {0}\n".format(ptm.project) +
        u"Completed for 1 project(s).\n",
        ""
    )

    assert capsys.readouterr() == exp


def test_cache(monkeypatch, ptm):
    """Test that passing the cache param calls the right summary method"""

    calls = []
    def mock_cache(project):
        calls.append("mock cache for {0}".format(project))
    monkeypatch.setattr(summary, "cache_test_summaries", mock_cache)

    call_populate_summary_cache(cache=True, project=ptm.project)
    assert calls[0] == "mock cache for {0}".format(ptm.project)


def test_build_and_cache(monkeypatch, ptm):
    """Test that passing the cache and build params calls both methods"""

    calls = []
    def mock_build(project):
        calls.append("mock build for {0}".format(project))
    monkeypatch.setattr(summary, "build_test_summaries", mock_build)

    def mock_cache(project):
        calls.append("mock cache for {0}".format(project))
    monkeypatch.setattr(summary, "cache_test_summaries", mock_cache)

    call_populate_summary_cache(cache=True, build=True, project=ptm.project)


    assert set(calls) == set(["mock cache for {0}".format(ptm.project),
                              "mock build for {0}".format(ptm.project)])


def test_single_batch_success(capsys, monkeypatch):
    """Test that you can populate summary cache with a single batch"""
    # create a set of projects
    create_project("foo", "medium")
    create_project("bar", "medium")

    # intercept the call for each project
    calls = []
    def mock_cache(project):
        calls.append("mock cache for {0}".format(project))
    monkeypatch.setattr(summary, "cache_test_summaries", mock_cache)

    try:
        call_populate_summary_cache(cache=True, cron_batches=["medium"])
    except SystemExit:
        assert False, capsys.readouterr()

    assert set(calls) == set(["mock cache for foo", "mock cache for bar"])

    exp = (
        u"Starting for projects: foo, bar\n" +
        u"Processing project foo\n" +
        u"Processing project bar\n" +
        u"Completed for 2 project(s).\n",
        ""
        )

    assert capsys.readouterr() == exp


def test_multiple_batches_success(capsys, monkeypatch):
    """test that you can populate the summary cache with multiple batches."""

    create_project("foo", "medium")
    create_project("bar", "medium")
    create_project("baz", "large")

    # intercept the call for each project
    calls = []
    def mock_cache(project):
        calls.append("mock cache for {0}".format(project))
    monkeypatch.setattr(summary, "cache_test_summaries", mock_cache)

    try:
        call_populate_summary_cache(
            cache=True,
            cron_batches=["medium", "large"],
            )
    except SystemExit:
        assert False, capsys.readouterr()

    assert set(calls) == set([
        "mock cache for foo",
        "mock cache for bar",
        "mock cache for baz",
        ])

    exp = (
        u"Starting for projects: foo, bar, baz\n"
        u"Processing project foo\n"
        u"Processing project bar\n"
        u"Processing project baz\n"
        u"Completed for 3 project(s).\n",
        ""
        )

    assert capsys.readouterr() == exp


def test_view_batches(capsys, ptm):
    # view projects that exist in each batch
    create_project("foo", "medium")
    create_project("bar", "medium")
    create_project("baz", "large")
    create_project("noo", None)

    call_populate_summary_cache(
        view_batches=True,
        )

    exp = (
        u"None: noo\n"
        u"large: baz\n"
        u"medium: foo, bar\n"
        u"small: {0}\n".format(ptm.project),
        ""
        )

    assert capsys.readouterr() == exp


def test_both_project_and_cron_branch_defined(capsys):
    """Shows project and cron_batch cannot both be defined."""

    with pytest.raises(SystemExit):
        call_populate_summary_cache(project="foo", cron_batches=["medium"])

    exp = (
        "",
        "Error: You must provide either project or cron_batch, but not both.\n",
        )

    assert capsys.readouterr() == exp


