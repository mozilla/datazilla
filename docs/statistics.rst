Statistics
==========

These are a set of webservice endpoints for getting data about a Datazilla
project.


Object Store
------------

.. http:get:: /(project)/stats/objectstore/error_count

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

        GET /talos/stats/objectstore/error_count?days_ago=10

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


.. http:get:: /(project)/stats/objectstore/error_list

    Return a list of all objectstore entries for this project that have an error.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.  This acts on the
        ``date_loaded`` field in the objectstore database.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.


    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/objectstore/error_list?days_ago=10

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


.. http:get:: /(project)/stats/objectstore/json_blob/(int:id)

    Return the full JSON blob for ``id`` as retrieved by the
    ``/(project)/stats/objectstore/error_list`` endpoint.  Often this JSON is
    in a non-parseable state.  So the information you're looking for may
    require you to dig into the poorly formed JSON without a parser.

    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/objectstore/json_blob/12845

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {"test_machine": {"name": "talos-r3-leopard-014", "os": "mac",
        "osversion": "OS X 10.5.8", "platform": "x86"}, "test_build":
        {"name": "Firefox", "version": "14.0.1", "revision": "b96eb495bfe5",
        ...


.. http:get:: /(project)/stats/objectstore/db_size

    Return size (in MegaBytes) of the objectstore database for this project.

    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/objectstore/db_size

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
-----------------

.. http:get:: /(project)/stats/perftest/runs_by_branch

    Return a list of test runs broken down by branch.

    :query days_ago: (required) Number of days prior to this date to use as the
        beginning of the date range for this request.
    :query numdays: (optional) Number of days worth of data to return.  If not
        provided, the date range will be from ``days_ago`` to today.
    :query show_test_runs: (optional) If set to ``true`` then show all the test
        run detail.  If omitted, or set to ``false`` then show only counts.


    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/perftest/runs_by_branch?days_ago=5

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

        GET /talos/stats/perftest/runs_by_branch?days_ago=5&show_test_runs=true

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


.. http:get:: /(project)/stats/perftest/ref_data/(table)

    Return a raw list of data from the ``table`` provided.  Valid ``table``
    values are: ``machines``, ``operating_systems``, ``options``,
    ``tests, pages``, ``products``

    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/perftest/ref_data/operating_systems

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        {
            "macOS X 10.5.8": 5,
            "win6.1.7600": 8,
            "linuxfedora 12": 4,
            ...
        }


.. http:get:: /(project)/stats/perftest/db_size

    Return size (in MegaBytes) of the perftest database for this project.

    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/perftest/db_size

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
---------

.. http:get:: /(project)/stats/pushlog/not_referenced

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

        GET /talos/stats/pushlog/not_referenced/?days_ago=100&branches=Mozilla-Inbound

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


.. http:get:: /(project)/stats/pushlog/branches

    Return the list of known pushlog branches.

    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/pushlog/branches

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            "Firefox",
            "Mozilla-Inbound",
            ...
        ]


.. http:get:: /(project)/stats/pushlog/db_size

    Return size (in MegaBytes) of the pushlog database for this project.

    **Example request**:

    .. sourcecode:: http

        GET /talos/stats/pushlog/db_size

    **Example response**:

    .. sourcecode:: http

        Content-Type: application/json

        [
            {
                "size_mb": "29.30",
                "db_name": "pushlog_hgmozilla_1"
            }
        ]

