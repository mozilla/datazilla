"""
Functions for sample pushlog data.

"""

import json

def get_pushlog_json_readable(json_data):
    """Return a handle to a readable object pointint to ``json_data``."""
    class Readable(object):
        def read(self):
            return json_data
    return Readable()


def get_pushlog_json_set():
    return json.dumps(get_pushlog_dict_set())


def get_pushlog_dict_set():
    return {

        "23046": {
            "date": 1341451081,
            "changesets": [
                    {
                    "node": "785345035a3ba70e7b8a9d1cf6b1e939416fe6f8",
                    "files": [
                        "content/xbl/src/nsXBLBinding.cpp",
                        "dom/base/nsDOMClassInfo.cpp",
                        "js/xpconnect/src/XPCWrappedNativeJSOps.cpp"
                    ],
                    "tags": [ ],
                    "author": "Bill McCloskey <wmccloskey@mozilla.com>",
                    "branch": "default",
                    "desc": "Bug 770759 - Add mutable handles (r=bhackett)"
                }
            ],
            "user": "wmccloskey@mozilla.com"
        },
        "23049": {
            "date": 1341455666,
            "changesets": [
                    {
                    "node": "fbd96a0bcc002b25656174adc1a499ced1df7f70",
                    "files": [
                        "js/src/frontend/Parser.cpp",
                        "js/src/vm/ScopeObject.h"
                    ],
                    "tags": [ ],
                    "author": "Bill McCloskey <wmccloskey@mozilla.com>",
                    "branch": "default",
                    "desc": "Bug 771018 - Replace \"const Shape\" with \"Shape\" (r=luke)"
                },
                    {
                    "node": "fe305819d2f26c9dbef649f0de0088152476209c",
                    "files": [
                        "js/src/jsapi.cpp",
                        "js/src/vm/ScopeObject.cpp"
                    ],
                    "tags": [ ],
                    "author": "Bill McCloskey <wmccloskey@mozilla.com>",
                    "branch": "default",
                    "desc": "Bug 771026 - Replace JSProperty with Shape (r=bhackett)"
                }
            ],
            "user": "wmccloskey@mozilla.com"
        },
        "23052": {
            "date": 1341494821,
            "changesets": [
                    {
                    "node": "ea890a6eed56fbbdc4fc721cbd11cafe2c329c4d",
                    "files": [
                        "browser/devtools/shared/DeveloperToolbar.jsm"
                    ],
                    "tags": [ ],
                    "author": "Joe Walker <jwalker@mozilla.com>",
                    "branch": "default",
                    "desc": "Bug 761481 - GCLI help output does not display the first time; r=dcamp"
                },
                    {
                    "node": "bd74a29499299ad9028a03baa468e5caad621198",
                    "files": [
                        "browser/devtools/commandline/gcli.jsm",
                        "browser/devtools/shared/DeveloperToolbar.jsm"
                    ],
                    "tags": [ ],
                    "author": "Joe Walker <jwalker@mozilla.com>",
                    "branch": "default",
                    "desc": " Bug 769234 - [devtb] GCLI has focus issues when embedded in firefox; r=dcamp"
                },
                    {
                    "node": "5d6c06259bb182efb5007e63e22a740491020ec1",
                    "files": [
                        "browser/app/profile/firefox.js",
                        "browser/base/content/browser-menubar.inc",
                        "browser/base/content/browser-sets.inc",
                        "browser/locales/en-US/chrome/browser/browser.dtd"
                    ],
                    "tags": [ ],
                    "author": "Joe Walker <jwalker@mozilla.com>",
                    "branch": "default",
                    "desc": "Bug 768150 - The developer toolbar should be preffed on by default for testing on nightly only; r=ttaubert"
                },
                    {
                    "node": "7209f9f14a7d9c53d0f1be3dde40ac495c38cc89",
                    "files": [ ],
                    "tags": [ ],
                    "author": "Tim Taubert <tim.taubert@gmx.de>",
                    "branch": "default",
                    "desc": "merge m-c to fx-team"
                }
            ],
            "user": "tim.taubert@gmx.de"
        }

    }
