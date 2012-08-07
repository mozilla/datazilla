from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.stats",

    (r"^objectstore/error_count$", "objectstore_views.get_error_count"),

    (r"^objectstore/error_list$", "objectstore_views.get_error_list"),

    (r"^objectstore/json_blob/(?P<id>\d+)/$", "objectstore_views.get_json_blob"),

    (r"^perftest/runs_by_branch/$", "perftest_views.get_runs_by_branch"),

    (r"^perftest/ref_data/(?P<table>\w+)/$", "perftest_views.get_ref_data"),

    )
