from django.conf.urls.defaults import *

urlpatterns = patterns(
    "datazilla.webapp.apps.datazilla.refdata",

    # pushlog
    (r"^pushlog/list/?$", "pushlog_views.get_pushlogs"),

    (r"^pushlog/branches/?$", "pushlog_views.get_all_branches"),

    (r"^pushlog/branch_uri/?$", "pushlog_views.get_branch_uri"),

    (r"^pushlog/db_size/?$", "pushlog_views.get_db_size"),

    )
