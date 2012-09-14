from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.testdata",

    (r"^raw/(?P<branch>.+)/(?P<revision>\w+)/?$", "views.get_testdata"),

    (r"^metrics/(?P<branch>.+)/(?P<revision>\w+)/?$", "views.get_metrics_data"),
    )
