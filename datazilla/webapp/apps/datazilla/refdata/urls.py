from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.refdata",

    # objectstore
    (r"^objectstore/error_count/?$", "objectstore_views.get_error_count"),

    (r"^objectstore/error_list/?$", "objectstore_views.get_error_list"),

    (r"^objectstore/json_blob/revisions/?$", "objectstore_views.get_json_blob_by_revisions"),

    (r"^objectstore/json_blob/(?P<id>\d+)/?$", "objectstore_views.get_json_blob"),

    (r"^objectstore/json_blob/test_run/(?P<test_run_id>\d+)/?$",
        "objectstore_views.get_json_blob_by_test_run_id"),

    (r"^objectstore/db_size/?$", "objectstore_views.get_db_size"),

    # perftest
    (r"^perftest/runs_by_branch/?$", "perftest_views.get_runs_by_branch"),

    (r"^perftest/ref_data/(?P<table>\w+)/?$", "perftest_views.get_ref_data"),

    (r"^perftest/db_size/?$", "perftest_views.get_db_size"),

    # pushlog
    (r"^pushlog/not_referenced/?$", "pushlog_views.get_not_referenced"),

    )
