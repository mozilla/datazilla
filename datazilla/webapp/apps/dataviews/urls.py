from django.conf.urls.defaults import *
from datazilla.webapp.apps.dataviews import views

urlpatterns = patterns('',
                       #UI Application
                       (r'^$', views.graphs),

                       #Web service methods used by the UI
                       (r'^api/(?P<method>\w+)/?$', views.dataview),

                       #UI Application help
                       (r'^help/?$', views.get_help),

                       )
