from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla.stats import views

urlpatterns = patterns('',

    (r'^count$', views.get_count_errors),

    )
