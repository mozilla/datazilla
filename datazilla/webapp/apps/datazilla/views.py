import datetime
import json
import urllib
import zlib

import oauth2 as oauth

import memcache

from django.shortcuts import render_to_response
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

from datazilla.model import PerformanceTestModel
from datazilla.model import utils
from datazilla.model import DatasetNotFoundError
from datazilla.model import DataSource

APP_JS = 'application/json'

##Decorators##
def oauth_required(func):
    """
    Decorator for views to ensure that the user is sending an OAuth signed
    request.  View methods that use this method a project kwarg.
    """
    def _wrap_oauth(request, *args, **kwargs):
        project = kwargs.get('project', None)

        ###
        # Until the production environment for talos can make use of
        # OAuth or use API/Keys we need to bypass OAuth to injest data.
        # This needs to be removed as soon as talos can support OAuth.
        ###
        if project in ['talos', 'views']:
            return func(request, *args, **kwargs)

        dm = PerformanceTestModel(project)

        #Get the consumer key
        key = request.REQUEST.get('oauth_consumer_key', None)

        if key is None:
            result = {"status": "No OAuth credentials provided."}
            return HttpResponse(
                json.dumps(result), content_type=APP_JS, status=403)

        try:
            #Get the consumer secret stored with this key
            ds_consumer_secret = dm.get_oauth_consumer_secret(key)
        except DatasetNotFoundError:
            result = {"status": "Unknown project '%s'" % project}
            return HttpResponse(
                json.dumps(result), content_type=APP_JS, status=404)

        #Construct the OAuth request based on the django request object
        req_obj = oauth.Request(request.method,
                                request.build_absolute_uri(),
                                request.REQUEST,
                                '',
                                False)

        server = oauth.Server()

        #Get the consumer object
        cons_obj = oauth.Consumer(key, ds_consumer_secret)

        #Set the signature method
        server.add_signature_method(oauth.SignatureMethod_HMAC_SHA1())

        try:
            #verify oauth django request and consumer object match
            server.verify_request(req_obj, cons_obj, None)
        except oauth.Error:
            status = 403
            result = {"status": "Oauth verification error."}
            return HttpResponse(
                json.dumps(result), content_type=APP_JS, status=status)

        return func(request, *args, **kwargs)

    return _wrap_oauth

@oauth_required
def set_test_data(request, project=""):
    """
    Post a JSON blob of data for the specified project.

    Store the JSON in the objectstore where it will be held for
    later processing.

    """
    #####
    #This conditional provides backwords compatibility with
    #the talos production environment.  It should
    #be removed after the production environment
    #is uniformaly using the new url format.
    ####
    if project == 'views':
        project = 'talos'

    # default to bad request if the JSON is malformed or not present
    status = 400

    try:
        json_data = request.POST['data']
    except KeyError:
        result = {"status":"No POST data found"}
    else:
        unquoted_json_data = urllib.unquote(json_data)

        error = None

        try:
            json.loads( unquoted_json_data )
        except ValueError as e:
            error = "Malformed JSON: {0}".format(e.message)
            result = {"status": "Malformed JSON", "message": error}
        else:
            result = {
                "status": "well-formed JSON stored",
                "size": len(unquoted_json_data),
            }

        try:
            dm = PerformanceTestModel(project)
            id = dm.store_test_data(unquoted_json_data, error)
            dm.disconnect()
        except Exception as e:
            status = 500
            result = {"status": "Unknown error", "message": str(e)}
        else:

            location = "/{0}/refdata/objectstore/json_blob/{1}".format(
                project, str(id)
                )

            result['url'] = request.build_absolute_uri(location)

            if not error:
                status = 200


    return HttpResponse(json.dumps(result), mimetype=APP_JS, status=status)

def homepage(request):

    template_context = {
        'DEBUG':settings.DEBUG,
        'PROJECTS':DataSource.objects.filter(
            contenttype="perftest").values_list("project", flat=True)
        }

    return render_to_response(
        'homepage.html', template_context
        )

