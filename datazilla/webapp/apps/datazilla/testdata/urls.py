from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.testdata",

    (r"^raw/(?P<branch>.+)/(?P<revision>[a-zA-Z0-9_.-]+)/?$", "views.get_testdata"),

    (r"^all_data/?$", "views.get_data_all_dimensions"),

    (r"^platforms_tests/?$", "views.get_platforms_and_tests"),

    (r"^all_data_date_range/?$", "views.get_all_data_date_range"),

    (r"^test_values/?$", "views.get_test_value_summary"),

    (r"^metrics/(?P<branch>.+)/(?P<revision>\w+)/pushlog/?$",
        "views.get_metrics_pushlog"),

    (r"^metrics/(?P<branch>.+)/(?P<revision>\w+)/summary/?$",
        "views.get_metrics_summary"),

    (r"^metrics/(?P<revision>\w+)/log/?$",
        "views.get_application_log"),

    (r"^metrics/(?P<branch>.+)/(?P<revision>\w+)/?$",
        "views.get_metrics_data"),

    )
