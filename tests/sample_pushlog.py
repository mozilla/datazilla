"""
Functions for sample pushlog data.

"""

import os

def pushlog_json():
    f = open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "pushlog_test.json",
        ))
    return f.read()
