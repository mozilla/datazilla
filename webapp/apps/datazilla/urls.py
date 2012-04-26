from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla import views

urlpatterns = patterns('',
                       (r'^$', views.graphs),
                       (r'^help$', views.getHelp),
                       (r'^api/get_date_range$', views.getDateRange),
                       (r'^api/.*$', views.dataview),
)
