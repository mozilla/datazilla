from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.stats",

    # objectstore
    (r"^objectstore/error_count$", "objectstore_views.get_error_count"),

    (r"^objectstore/error_list$", "objectstore_views.get_error_list"),

    (r"^objectstore/json_blob/(?P<id>\d+)/$", "objectstore_views.get_json_blob"),

    (r"^objectstore/db_size$", "objectstore_views.get_db_size"),

    # perftest
    (r"^perftest/runs_by_branch/$", "perftest_views.get_runs_by_branch"),

    (r"^perftest/ref_data/(?P<table>\w+)/$", "perftest_views.get_ref_data"),

    (r"^perftest/db_size$", "perftest_views.get_db_size"),

    # pushlog
    (r"^pushlog/not_referenced/$", "pushlog_views.get_not_referenced"),

    (r"^pushlog/db_size$", "pushlog_views.get_db_size"),

    )
