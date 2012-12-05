from django.conf.urls.defaults import *
from datazilla.webapp.apps.summary import summary_view

urlpatterns = patterns('',
                       #UI Application
                       (r'^$', summary_view.summary_page),

                       (r"^(?P<branch>.+)/(?P<revision>\w+)/?$",
                            summary_view.summary_page),
                       )
