"""
Tests for management command to update pushlogs.

"""
from contextlib import contextmanager
from cStringIO import StringIO
import json
import os
from tempfile import mkstemp

from django.core.management import call_command

#from mock import patch




"""Tests for update_pushlog management command."""

"""
Will have to patch the pushlogmodel.get_all_branches method to return a
small set (2 perhaps, maybe just 1) branch names.

Then will have to patch the calls for pushlogs so it returns sample data.
Then import them
Then check the table.  May need a way to check the table.  PushLogModel will need some getters, perhaps.

"""

def call_command(*args):
    """
    Runs the management command and returns (stdout, stderr) output.

    Also patch ``sys.exit`` so a ``CommandError`` doesn't cause an exit.

    """
    with patch("sys.stdout", StringIO()) as stdout:
        with patch("sys.stderr", StringIO()) as stderr:
            with patch("sys.exit"):
                call_command("import", *args)

    stdout.seek(0)
    stderr.seek(0)
    return (stdout.read(), stderr.read())


@contextmanager
def tempfile(self, contents):
    """
    Write given contents to a temporary file, yielding its path.

    Used as a context manager; automatically deletes the temporary file
    when context manager exits.

    """
    (fd, path) = mkstemp()
    fh = os.fdopen(fd, "w")
    fh.write(contents)
    fh.close()

    try:
        yield path
    finally:
        os.remove(path)


def xtest_no_args(self):
    """Command shows usage."""
    output = call_command()

    self.assertEqual(
        output,
        (
            "",
            "Error: Usage: <product_name> <product_version> <filename>\n",
            )
    )


