from django.conf.urls.defaults import patterns, include
from django.http import HttpResponse

from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
project_list = settings.ALLOWED_PROJECTS or '\w+'

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webapp.views.home', name='home'),
    # url(r'^webapp/', include('webapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    (r'^robots\.txt$', lambda r: HttpResponse(
        "User-agent: *\nDisallow: /", mimetype="text/plain"
        )),

    #default UI
    (r'^/?$', include('datazilla.webapp.apps.datazilla.urls')),

    (r'^b2g/?', include('datazilla.webapp.apps.summary.b2g_app_urls')),

    (r'^(?P<project>{0})/?$'.format(project_list), include('datazilla.webapp.apps.dataviews.urls')),

    #dataview application
    (r'^(?P<project>{0})/dataviews/?'.format(project_list), include('datazilla.webapp.apps.dataviews.urls')),


    (r'^(?P<project>{0})/summary/?'.format(project_list), include('datazilla.webapp.apps.summary.urls')),

    #datazilla web service
    (r'^(?P<project>{0})/?'.format(project_list), include('datazilla.webapp.apps.datazilla.urls')),

    #api for data ingestion
    (r'^(?P<project>{0})/api/?'.format(project_list), include('datazilla.webapp.apps.datazilla.urls')),

    # return reference data about Datazilla, not particular to a project
    (r'^refdata/', include("datazilla.webapp.apps.datazilla.refdata.urls_no_project")),


    )
