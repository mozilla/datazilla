from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla import views

urlpatterns = patterns('',
                       #UI Application
                       (r'^$', views.graphs),

                       #UI Application help
                       (r'^help/?$', views.get_help),

                       #Loads JSON object into objectstore
                       (r'^api/load_test/?$', views.set_test_data),

                       #Web service methods used by the UI
                       (r'^api/(?P<method>\w+)/?$', views.dataview),

                       #return statistics about Datazilla
                       (r'^stats/', include("datazilla.webapp.apps.datazilla.stats.urls")),

                       #return test data for a project
                       (r'^testdata/', include("datazilla.webapp.apps.datazilla.testdata.urls")),
                       )
