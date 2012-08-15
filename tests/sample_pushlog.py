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


def get_pushlog_json_set1():
    return json.dumps(get_pushlog_dict_set1())


def get_pushlog_dict_set1():
    return {

        "23046": {
            "date": 1341451081,
            "changesets": [
                    {
                    "node": "13897ce0f3a2a70e7b8a9d1cf6b1e939416fe6f8",
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


def get_pushlog_json_set2():
    return """{

        "21804": {
            "date": 1325815064,
            "changesets": [
                {
                    "node": "8b0437df0da3682206e3a37a43b2d49c92618442",
                    "files": [
                        "dom/workers/RuntimeService.cpp"
                    ],
                    "tags": [ ],
                    "author": "Ben Turner <bent.mozilla@gmail.com>",
                    "branch": "default",
                    "desc": "Bug 715756: Workers: Enable TI and allow JIT hardening to be disabled. r=sicking."
                }
            ],
            "user": "bturner@mozilla.com"
        },
        "21805": {
            "date": 1325817942,
            "changesets": [
                {
                    "node": "c7e27452a143c834a4d1d7acf8c202261504210c",
                    "files": [
                        "mobile/android/base/ui/PanZoomController.java"
                    ],
                    "tags": [ ],
                    "author": "Kartikaya Gupta <kgupta@mozilla.com>",
                    "branch": "default",
                    "desc": "Bug 715164 - Guard against another race condition in PZC. r=pcwalton"
                }
            ],
            "user": "pwalton@mozilla.com"
        },
        "21806": {
            "date": 1325843913,
            "changesets": [
                {
                    "node": "8ae16e346bd0c2c93711884b2a2e5db10060512d",
                    "files": [
                        "dom/indexedDB/Key.cpp"
                    ],
                    "tags": [ ],
                    "author": "Jan Varga <jan.varga@gmail.com>",
                    "branch": "default",
                    "desc": "Bug 715074 - SIGBUS on unaligned access in Key::EncodeNumber. r=sicking"
                }
            ],
            "user": "Jan.Varga@gmail.com"
        }
    }"""