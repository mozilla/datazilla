from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.stats",

    (r"^objectstore/error_count$", "views.get_error_count"),

    (r"^objectstore/error_list$", "views.get_error_list"),

    (r"^objectstore/json_blob/(?P<id>\d+)/$", "views.get_json_blob"),

    )
