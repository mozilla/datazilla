from django.conf.urls.defaults import *
from datazilla.webapp.apps.datazilla import views

urlpatterns = patterns('',

                       #Loads JSON object into objectstore
                       (r'^load_test/?$', views.set_test_data),

                       #return reference data
                       (r'^refdata/', include(
                            "datazilla.webapp.apps.datazilla.refdata.urls"
                        )),

                       #return test data for a project
                       (r'^testdata/', include(
                            "datazilla.webapp.apps.datazilla.testdata.urls"
                        )),
                       )
