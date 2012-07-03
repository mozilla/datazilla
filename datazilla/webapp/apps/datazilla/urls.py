from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla import views

urlpatterns = patterns('',
                       #UI Application
                       (r'^$', views.graphs),

                       #UI Application help
                       (r'^help$', views.get_help),

                       #Loads JSON object into objectstore
                       (r'^api/load_test$', views.set_test_data),

                       #Web service methods used by the UI
                       (r'^api/(?P<method>\w+)$', views.dataview),
)
