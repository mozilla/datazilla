from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.testdata",

    (r"^(?P<branch>.+)/(?P<revision>\w+)/?$", "views.get_testdata"),

    )
