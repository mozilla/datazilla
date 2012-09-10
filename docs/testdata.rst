Test Data
==========

These are a set of webservice endpoints for getting the actual raw test data
for a given project.


Test Data
---------

.. http:get:: /(project)/testdata/raw/(branch)/(revision)/

    Return a list of the test data for the ``branch`` and ``revision`` for
    the specified ``project``.

    If a JSON blob of test data is malformed, or has an error, then
    a placeholder with the error message is returned.

    :query test_name: (optional) The name of the test to filter on.
    :query os_name: (optional) The name of the operating system to
        filter on.

    **Example request**:

    .. sourcecode:: http

        GET http://localhost:8000/talos/testdata/raw/Mozilla-Beta/ebfad1bf8749/
        GET http://localhost:8000/talos/testdata/raw/Mozilla-Beta/ebfad1bf8749/?os_name=mac&test_name=Talos%20tpaint

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [

            {
                "results_aux": { },
                "test_machine": {
                    "platform": "x86_64",
                    "osversion": "OS X 10.6.8",
                    "os": "mac",
                    "name": "talos-r4-snow-074"
                },
                "testrun": {
                    "date": "1342729660",
                    "suite": "Talos tscroll.2",
                    "options": {
                        "responsiveness": false,
                        "tpmozafterpaint": false,
                        ...
                    }
                },
                "results": {
                    "tiled.html": [
                        14522,
                        10408,
                        10414,
                        10414,
                        10372
                    ],
                    "iframe.svg": [
                        11941,
                        11474,
                        12153,
                        12451,
                        11686
                    ],
                    ...
                },
                "test_build": {
                    "id": "20120719120951",
                    "version": "15.0",
                    "name": "Firefox",
                    "branch": "Mozilla-Beta",
                    "revision": "ebfad1bf8749"
                }
            },
            { … },
            { … },
            { … },
            { … }

        ]

.. http:get:: /(project)/testdata/metrics/(branch)/(revision)/

    Return metrics data for the ``branch`` and ``revision`` for
    the specified ``project``.

    :query test_name: (optional) The name of the test to filter on.
    :query os_name: (optional) The name of the operating system to
        filter on.

    **Example request**:

    .. sourcecode:: http

        GET http://localhost:8000/talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/
        GET http://localhost:8000/talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/?os_name=mac&test_name=Talos%20tpaint

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {"stuff": "things"}
