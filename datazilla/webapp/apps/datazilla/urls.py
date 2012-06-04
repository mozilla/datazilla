from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla import views

urlpatterns = patterns('',
                       (r'^$', views.graphs),
                       (r'^help$', views.get_help),
                       (r'^load_test$', views.set_test_data),
                       (r'^api/(?P<method>\w+)$', views.dataview),
)
