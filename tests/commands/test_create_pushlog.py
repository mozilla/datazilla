"""
Tests for management command to create pushlog database.

"""

from django.core.management import call_command
from datazilla.model.base import PushLogModel



def call_create_pushlog(*args, **kwargs):
    call_command("create_pushlog", *args, **kwargs)


def test_no_args(capsys):
    """Shows need for a host."""
    call_create_pushlog()

    exp = (
        "You must supply a host name for the pushlog database: --host hostname\n",
        "",
        )

    assert capsys.readouterr() == exp


def test_successful_create(capsys, monkeypatch):
    """Successful create call on pushlog database."""

    @classmethod
    def mock_create(justme, host, type):
        class MyFoo(object):
            def disconnect(self):
                pass
        return MyFoo()
    monkeypatch.setattr(PushLogModel, "create", mock_create)

    call_create_pushlog(host="foo_host")

    exp = (
        "Pushlog database created on foo_host\n",
        "",
        )

    assert capsys.readouterr() == exp
