"""
Functions for sample pushlog data.

"""

import os

def pushlog_json():
    """Return the contents of the pushlog_test.json file"""
    return pushlog_json_file().read()


def pushlog_json_file():
    """Return a handle to the pushlog_test.json file."""

    return open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "pushlog_test.json",
        ))

def pushlog_json_empty():
    """Return a handle to an empty buffer"""
    class Readable(object):
        def read(self):
            return ""
    return Readable()