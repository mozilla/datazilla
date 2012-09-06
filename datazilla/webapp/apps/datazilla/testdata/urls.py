from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.testdata",

    (r"^(?P<branch>\w+)/(?P<revision>\w+)/?$", "views.get_testdata"),

    )
