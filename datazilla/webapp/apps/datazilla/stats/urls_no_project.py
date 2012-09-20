from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.stats",

    # pushlog
    (r"^pushlog/list/?$", "pushlog_views.get_pushlogs"),

    (r"^pushlog/branches/?$", "pushlog_views.get_all_branches"),

    (r"^pushlog/db_size/?$", "pushlog_views.get_db_size"),

    )
