Web Service
==========

The web services available in datazilla can be grouped into the following categories.

Test Data
---------

These are a set of webservice endpoints for getting the raw test data
for a given project.

.. http:get:: /(project)/testdata/raw/(branch)/(revision)/

    Return a list of the test data for the ``project``, ``branch`` and ``revision`` specified.

    If a JSON blob of test data is malformed, or has an error, then
    a placeholder with the error message is returned.

    :query os_name: (optional) The name of the operating system to filter on.
        *Examples:* ``win``, ``mac``, ``linux``

    :query os_version: (optional) The operating system version associated with an ``os_name`` to filter on.
        *Examples:* ``OSX 10.5.8``, ``fedora 12``, ``5.1.2600``

    :query branch_version: (optional) The branch version associated with ``brach_version`` to filter on.
        *Examples:* ``15.0``, ``16.0a1``, ``15.0.1``

    :query processor: (optional) The name of the processor associated with the test run.
        *Examples:* ``x86_64``, ``x86``, ``arm``

    :query build_type: (optional) The type of build.
        *Examples:* ``opt``, ``debug``

    :query test_name: (optional) The name of the test to filter on.  Test names are prefixed with their type.
        *Examples:* ``Talos tp5row``, ``Talos tsvg``, ``Talos tdhtml``

    :query page_name: (optional) The page name associated with the test.
        *Examples:* ``scrolling.html``, ``layers6.html``, ``digg.com``


        **All parameters can take a comma delimited list of arguments.**


    **Example request**:

    .. sourcecode:: http

        GET /talos/testdata/raw/Mozilla-Beta/ebfad1bf8749/
        GET /talos/testdata/raw/Mozilla-Beta/ebfad1bf8749?os_name=mac&test_name=Talos%20tp5row
        GET /talos/testdata/raw/Mozilla-Beta/ebfad1bf8749?os_name=mac,linux
        GET /talos/testdata/raw/Mozilla-Beta/ebfad1bf8749?page_name=digg.com,alipay.com,tmall.com

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

Metrics Data
------------
These are a set of web service endpoints for retrieving metrics data.

.. http:get:: /(project)/testdata/metrics/(branch)/(revision)

    Return all metrics data for the ``project``, ``branch`` and ``revision`` specified.

    :query os_name: (optional) The name of the operating system to filter on.
        *Examples:* ``win``, ``mac``, ``linux``

    :query os_version: (optional) The operating system version associated with an ``os_name`` to filter on.
        *Examples:* ``OSX 10.5.8``, ``fedora 12``, ``5.1.2600``

    :query branch_version: (optional) The branch version associated with ``brach_version`` to filter on.
        *Examples:* ``15.0``, ``16.0a1``, ``15.0.1``

    :query processor: (optional) The name of the processor associated with the test run.
        *Examples:* ``x86_64``, ``x86``, ``arm``

    :query build_type: (optional) The type of build.
        *Examples:* ``opt``, ``debug``

    :query test_name: (optional) The name of the test to filter on.  Test names are prefixed with their type.
        *Examples:* ``Talos tp5row``, ``Talos tsvg``, ``Talos tdhtml``

    :query page_name: (optional) The page name associated with the test.
        *Examples:* ``scrolling.html``, ``layers6.html``, ``digg.com``


        **All parameters can take a comma delimited list of arguments.**

    **Example request**:

    .. sourcecode:: http

        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/
        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749?os_name=mac&test_name=Talos%20tp5row
        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749?os_name=mac,linux
        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749?page_name=digg.com,alipay.com,tmall.com

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            {
                "pages": {

                    "icanhascheezburger.com": {
                        "push_date": 1345523670,
                        "trend_stddev": 49.8,
                        "h0_rejected": false,
                        "p": 0.6,
                        "fdr": false,
                        "stddev": 12.3,
                        "pushlog_id": 6077315,
                        "trend_mean": 268.5,
                        "mean": 265.7,
                        "test_evaluation": true,
                        "n_replicates": 25
                    },
                    "ucoz.ru": {
                        "push_date": 1345523670,
                        "trend_stddev": 2.4,
                        "h0_rejected": false,
                        "p": 0.6,
                        "fdr": false,
                        "stddev": 1.9,
                        "pushlog_id": 6077315,
                        "trend_mean": 73.7,
                        "mean": 73.5,
                        "test_evaluation": true,
                        "n_replicates": 25
                    },
                    "digg.com": {
                        "push_date": 1345523670,
                        "trend_stddev": 3.1,
                        "h0_rejected": false,
                        "p": 0.2,
                        "fdr": false,
                        "stddev": 3.3,
                        "pushlog_id": 6077315,
                        "trend_mean": 151.6,
                        "mean": 152.2,
                        "test_evaluation": true,
                        "n_replicates": 25
                    },
                    { … },
                    { … },
                    { … },
                    ...
                },

                "test_machine": {
                    "platform": "x86",
                    "osversion": "6.1.7600",
                    "os": "win",
                    "name": "talos-r3-w7-060"
                },
                "testrun": {
                    "date": 1348091605,
                    "suite": "Talos tp5row",
                    "test_run_id": 417
                },
                "push_info": {
                    "pushlog_id": 6077315,
                    "push_date": 1345523670
                },
                "test_build": {
                    "name": "Firefox",
                    "version": "15.0",
                    "branch": "Mozilla-Beta",
                    "type": "opt",
                    "id": "20120820213501",
                    "revision": "7d3fc54fb002"
                }

            },
            { … },
            { … },
            { … },
            ...
        ]

.. http:get:: /(project)/testdata/metrics/(branch)/(revision)/summary

    Return a summary of all test evaluation results for all metrics data associated
    with the ``project``, ``branch`` and ``revision`` specified.  A test evaluation is a generic
    representation of test sucess or failure.  A test evaluation of ``false`` indicates failure and ``true`` indicates
    sucess.  All metric methods available implement a generic test evaluation that can be accessed
    as the metric value ``test_evaluation``.

    :query os_name: (optional) The name of the operating system to filter on.
        *Examples:* ``win``, ``mac``, ``linux``

    :query os_version: (optional) The operating system version associated with an ``os_name`` to filter on.
        *Examples:* ``OSX 10.5.8``, ``fedora 12``, ``5.1.2600``

    :query branch_version: (optional) The branch version associated with ``brach_version`` to filter on.
        *Examples:* ``15.0``, ``16.0a1``, ``15.0.1``

    :query processor: (optional) The name of the processor associated with the test run.
        *Examples:* ``x86_64``, ``x86``, ``arm``

    :query build_type: (optional) The type of build.
        *Examples:* ``opt``, ``debug``

    :query test_name: (optional) The name of the test to filter on.  Test names are prefixed with their type.
        *Examples:* ``Talos tp5row``, ``Talos tsvg``, ``Talos tdhtml``

    :query page_name: (optional) The page name associated with the test.
        *Examples:* ``scrolling.html``, ``layers6.html``, ``digg.com``


        **All parameters can take a comma delimited list of arguments.**

    **Example request**:

    .. sourcecode:: http

        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/summary
        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/summary?os_name=mac&test_name=Talos%20tp5row
        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/summary?os_name=mac,linux
        GET /talos/testdata/metrics/Mozilla-Beta/ebfad1bf8749/smmary?page_name=digg.com,alipay.com,tmall.com

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {
            product_info": {
                "version": "15.0",
                "name": "Firefox",
                "branch": "Mozilla-Beta",
                "revision": "7d3fc54fb002"
            },
            summary": {
                "fail": {
                    "percent": 3,
                    "value": 25
                },
                "total_tests": 977,
                "pass": {
                    "percent": 97,
                    "value": 952
                }
            },
            summary_by_platform": {
                "linux fedora 12 x86": {
                    "fail": {
                        "percent": 1,
                        "value": 2
                    },
                    "total_tests": 140,
                    "pass": {
                        "percent": 99,
                        "value": 138
                    }
                },
                "linux redhat 12 x86": {
                    "fail": {
                        "percent": 0,
                        "value": 0
                    },
                    "total_tests": 131,
                    "pass": {
                        "percent": 100,
                        "value": 131
                    }
                },
                { ... },
                { ... },
                { ... },
            },
            summary_by_test": {
                "Talos tp5row": {
                    "fail": {
                        "percent": 1,
                        "value": 9
                    },
                    "total_tests": 660,
                    "pass": {
                        "percent": 99,
                        "value": 651
                    }
                },
                "Talos tsvg_opacity": {
                    "fail": {
                        "percent": 0,
                        "value": 0
                    },
                    "total_tests": 14,
                    "pass": {
                        "percent": 100,
                        "value": 14
                    }
                },
                { ... },
                { ... },
                { ... },
                ...
            },
            tests": {

                "Talos tp5row": {
                    "linux fedora 12 x86": {
                        "fail": {
                            "percent": 0,
                            "value": 0
                        },
                        "pass": {
                            "percent": 100,
                            "value": 91
                        }
                        "total_tests": 91,
                        "pages": [
                            { "telegraph.co.uk": true },
                            { "web.de": true },
                            { "tudou.com": true },
                            { "nicovideo.jp": true },
                            { "rakuten.co.jp": true },
                            { "store.apple.com": true },
                            { ... },
                            ...
                        ],
                        "platform_info": {
                            "operating_system_version": "fedora 12",
                            "type": "opt",
                            "processor": "x86",
                            "operating_system_name": "linux"
                        },
                    },
                    win 6.1.7600 x86": {
                        "fail": {
                            "percent": 7,
                            "value": 7
                        },
                        "pass": {
                            "percent": 93,
                            "value": 93
                        }
                        "total_tests": 100,
                        "pages": [
                            { "telegraph.co.uk": true },
                            { "web.de": true },
                            { "tudou.com": true },
                            { "nicovideo.jp": false },
                            { "rakuten.co.jp": true },
                            { "store.apple.com": false },
                            { ... },
                            ...
                        ],
                        "platform_info": {
                            "operating_system_version": "6.1.7600",
                            "type": "opt",
                            "processor": "x86",
                            "operating_system_name": "win"
                        },
                    },
                    { ... },
                     ...
                },
                "Talos tsvg_opacity": { ... },
                "Talos tsvg": { ... },
                "Talos tdhtml": { ... }
            }

.. http:get:: /(project)/testdata/metrics/(branch)/pushlog

    Return a pushlog data structure for the given ``project`` and ``branch`` combination
    decorated with all of the metrics data associated with each push.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.  This acts on the
        ``date_loaded`` field in the objectstore database.

    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.

    :query os_name: (optional) The name of the operating system to filter on.
        *Examples:* ``win``, ``mac``, ``linux``

    :query os_version: (optional) The operating system version associated with an ``os_name`` to filter on.
        *Examples:* ``OSX 10.5.8``, ``fedora 12``, ``5.1.2600``

    :query branch_version: (optional) The branch version associated with ``brach_version`` to filter on.
        *Examples:* ``15.0``, ``16.0a1``, ``15.0.1``

    :query processor: (optional) The name of the processor associated with the test run.
        *Examples:* ``x86_64``, ``x86``, ``arm``

    :query build_type: (optional) The type of build.
        *Examples:* ``opt``, ``debug``

    :query test_name: (optional) The name of the test to filter on.  Test names are prefixed with their type.
        *Examples:* ``Talos tp5row``, ``Talos tsvg``, ``Talos tdhtml``

    :query page_name: (optional) The page name associated with the test.
        *Examples:* ``scrolling.html``, ``layers6.html``, ``digg.com``


        **All parameters can take a comma delimited list of arguments.**

    **Example request**:

    .. sourcecode:: http

        GET /talos/testdata/metrics/Mozilla-Beta/pushlog
        GET /talos/testdata/metrics/Mozilla-Beta/pushlog?os_name=mac&test_name=Talos%20tp5row
        GET /talos/testdata/metrics/Mozilla-Beta/pushlog?os_name=mac,linux
        GET /talos/testdata/metrics/Mozilla-Beta/pushlog?page_name=digg.com,alipay.com,tmall.com

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            {
                "branch_name": "Mozilla-Beta",
                "pushlog_id": 6004901,
                "metrics_data": [ ... ],
                "date": 1345500867,
                "dz_revision": "6fc9e89951a9",
                "push_id": 1303,
                "revisions": [
                    "6fc9e89951a9"
                ]
            },
            {
                "branch_name": "Mozilla-Beta",
                "pushlog_id": 6034235,
                "metrics_data": [
                    {
                        "pages": {
                            "icanhascheezburger.com": {
                                "push_date": 1345510991,
                                "trend_stddev": 20.2,
                                "h0_rejected": false,
                                "p": 0.4,
                                "fdr": false,
                                "stddev": 23.7,
                                "pushlog_id": 6034235,
                                "trend_mean": 237.9,
                                "mean": 238.8,
                                "test_evaluation": true,
                                "n_replicates": 25
                            },
                            "ucoz.ru": {
                                "push_date": 1345510991,
                                "trend_stddev": 3.1,
                                "h0_rejected": false,
                                "p": 0.8,
                                "fdr": false,
                                "stddev": 1.6,
                                "pushlog_id": 6034235,
                                "trend_mean": 68.4,
                                "mean": 67.9,
                                "test_evaluation": true,
                                "n_replicates": 25
                            },
                            { ... },
                            { ... },
                            { ... },
                        },
                        "test_machine": {
                            "platform": "x86",
                            "osversion": "5.1.2600",
                            "os": "win",
                            "name": "talos-r3-xp-053"
                        },
                        "testrun": {
                            "date": 1348091605,
                            "suite": "Talos tp5row",
                            "test_run_id": 289
                        },
                        "push_info": {
                            "pushlog_id": 6034235,
                            "push_date": 1345510991
                        },
                        "test_build": {
                            "name": "Firefox",
                            "version": "15.0",
                            "branch": "Mozilla-Beta",
                            "type": "opt",
                            "id": "20120820180351",
                            "revision": "b691cd9c10dd"
                        }

                    },
                    { ... },
                    { ... },
                    { ... },
                ],
                "date": 1345510991,
                "dz_revision": "b691cd9c10dd",
                "push_id": 1304,
                "revisions": [
                    "31aacbde98ad",
                    "b691cd9c10dd"
                ]
            },
            {
                "branch_name": "Mozilla-Beta",
                "pushlog_id": 6077315,
                "metrics_data": [ ... ],
                "date": 1345523670,
                "dz_revision": "7d3fc54fb002",
                "push_id": 1305,
                "revisions": [
                    "7d3fc54fb002"
                ]
            },
            { ... },
            { ... },
            { ... },
        ]

},

Reference Data
----------

These are a set of web service endpoints for getting reference data about a Datazilla
project.


Object Store
^^^^^^^^^^^^

.. http:get:: /(project)/refdata/objectstore/error_count

    Return a count of all objectstore entries that have an error.  The return
    value is broken down by two types:

        * JSON parse errors
        * All other errors

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.  This acts on the
        ``date_loaded`` field in the objectstore database.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.

    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/objectstore/error_count?days_ago=10

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [

            {
                "count(id)": 36,
                "message": "Malformed JSON"
            },
            {
                "count(id)": 4,
                "message": "Other"
            }

        ]


.. http:get:: /(project)/refdata/objectstore/error_list

    Return a list of all objectstore entries for this project that have an error.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.  This acts on the
        ``date_loaded`` field in the objectstore database.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.


    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/objectstore/error_list?days_ago=10

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [

            {
                "date_loaded": 1343793738,
                "id": 127661,
                "test_run_id": null,
                "worker_id": null,
                "processed_flag": "ready",
                "error_msg": "Malformed JSON: Expecting , delimiter: line 1 column 52606 (char 52606)"
            },
            {
                "date_loaded": 1343795847,
                "id": 127678,
                "test_run_id": null,
                "worker_id": null,
                "processed_flag": "ready",
                "error_msg": "Malformed JSON: Expecting , delimiter: line 1 column 51298 (char 51298)"
            },
            ...
        ]


.. http:get:: /(project)/refdata/objectstore/json_blob/(int:id)

    Return the full JSON blob for ``id`` as retrieved by the
    ``/(project)/refdata/objectstore/error_list`` endpoint.  Often this JSON is
    in a non-parseable state.  So the information you're looking for may
    require you to dig into the poorly formed JSON without a parser.

    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/objectstore/json_blob/12845

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {"test_machine": {"name": "talos-r3-leopard-014", "os": "mac",
        "osversion": "OS X 10.5.8", "platform": "x86"}, "test_build":
        {"name": "Firefox", "version": "14.0.1", "revision": "b96eb495bfe5",
        ...


.. http:get:: /(project)/refdata/objectstore/db_size

    Return size (in MegaBytes) of the objectstore database for this project.

    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/objectstore/db_size

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [

            {
                "size_mb": "1740.55",
                "db_name": "talos_objectstore_1"
            }

        ]


Performance Tests
^^^^^^^^^^^^^^^^^^

.. http:get:: /(project)/refdata/perftest/runs_by_branch

    Return a list of test runs broken down by branch.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.
    :query show_test_runs: (optional) If set to ``true`` then show all the test
        run detail.  If omitted, or set to ``false`` then show only counts.


    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/perftest/runs_by_branch?days_ago=5

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {

            "Mozilla-Beta": {
                "count": 749
            }
            Mozilla-Beta-Release-Non-PGO": {
                "count": 510,
            }
        }


    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/perftest/runs_by_branch?days_ago=5&show_test_runs=true

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {

            "Mozilla-Beta": {
                "count": 749,
                "test_runs": [
                    {
                        "build_id": 2051,
                        "status": 1,
                        "date_run": 1344714939,
                        "test_id": 3,
                        "product": "Firefox",
                        "version": "15.0",
                        "branch": "Mozilla-Beta",
                        "machine_id": 555,
                        "id": 132895,
                        "revision": "50f5c2689179"
                    },
                    ...
                ]
            }
        }


.. http:get:: /(project)/refdata/perftest/ref_data/(data_type)

    Return a raw list of data from the ``data_type`` provided.  Valid ``data_type``
    values are: ``machines``, ``operating_systems``, ``options``,
    ``tests``, ``pages``, ``products``

    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/perftest/ref_data/operating_systems

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {
            "macOS X 10.5.8": 5,
            "win6.1.7600": 8,
            "linuxfedora 12": 4,
            ...
        }


.. http:get:: /(project)/refdata/perftest/db_size

    Return size (in MegaBytes) of the perftest database for this project.

    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/perftest/db_size

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            {
                    size_mb": "10289.78",
                    "db_name": "talos_perftest_1"
            }
        ]


Push Logs
^^^^^^^^^

.. http:get:: /(project)/refdata/pushlog/not_referenced

    Return a list of pushlog entries that are not reflected in the perftest data
    for ``project``.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.
    :query branches: (optional) Which branches to return un-referenced pushlogs.
        This can be a single branch, or a comma-separated list of branches.  If not
        provided, return data for all branches.


    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/pushlog/not_referenced/?days_ago=100&branches=Mozilla-Inbound

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {

            "with_matching_test_run": {
                "Mozilla-Inbound": {
                    "pushlogs": [
                        {
                            "push_id": 11171,
                            "revisions": [
                                "b4d033913a03",
                                "85d44a26763c",
                                "551ad0863475"
                            ]
                        },
                        ...
                    ]
                }
            },
            "without_matching_test_run": {
                "Mozilla-Inbound": {
                    "pushlogs": [
                        {
                            "push_id": 11078,
                            "revisions": [
                                "d592966ede4f"
                            ]
                        },
                        ...
                    ]
                }
            }
        }


.. http:get:: /(project)/refdata/pushlog/list

    Return a list of pushlog entries.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.
    :query branches: (optional) Which branches to return pushlogs.
        This can be a single branch, or a comma-separated list of branches.  If not
        provided, return data for all branches.


    **Example request**:

    .. sourcecode:: http

        GET /talos/refdata/pushlog/list/?days_ago=1&branches=Mozilla-Inbound

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {
            "14470": {
                "branch_name": "Mozilla-Inbound",
                "revisions": [
                    "41cf3c361d9d"
                ]
            },
            "14471": {
                "branch_name": "Mozilla-Inbound",
                "revisions": [
                    "fd4d9c386f97",
                    "8a11353cad22",
                    "a027c9d63d20",
                    "cb3dd01ba9be",
                    "14ac87e7546b",
                    "aa4ba0fc1f8d",
                    "1cc49d5dcff4",
                    "c6768c151b64"
                ]
            }
        }


.. http:get:: /refdata/pushlog/branches

    Return the list of known pushlog branches.

    **Example request**:

    .. sourcecode:: http

        GET /refdata/pushlog/branches

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            "Firefox",
            "Mozilla-Inbound",
            ...
        ]


.. http:get:: /refdata/pushlog/db_size

    Return size (in MegaBytes) of the pushlog database for this project.

    **Example request**:

    .. sourcecode:: http

        GET /refdata/pushlog/db_size

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            {
                "size_mb": "29.30",
                "db_name": "pushlog_hgmozilla_1"
            }
        ]

