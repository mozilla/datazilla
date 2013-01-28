from django.conf.urls.defaults import *
from datazilla.webapp.apps.summary import summary_view

urlpatterns = patterns('',
                       #UI Application
                       (r'^$', summary_view.apps_summary_page)
                       )
