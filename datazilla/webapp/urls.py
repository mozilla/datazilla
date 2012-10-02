from django.conf.urls.defaults import patterns, include

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webapp.views.home', name='home'),
    # url(r'^webapp/', include('webapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    #default UI
    (r'^(?P<project>\w+)/?$', include('datazilla.webapp.apps.dataviews.urls')),

    #dataview application
    (r'^(?P<project>\w+)/dataviews/?', include('datazilla.webapp.apps.dataviews.urls')),

    #revision metrics summary
    (r'^(?P<project>\w+)/summary/?', include('datazilla.webapp.apps.summary.urls')),


    #datazilla web service
    (r'^(?P<project>\w+)/?', include('datazilla.webapp.apps.datazilla.urls')),

    #api for data ingestion
    (r'^(?P<project>\w+)/api/?', include('datazilla.webapp.apps.datazilla.urls')),

    # return reference data about Datazilla, not particular to a project
    (r'^refdata/', include("datazilla.webapp.apps.datazilla.refdata.urls_no_project")),

    )
