import datetime
import json
import urllib
import zlib

from django.shortcuts import render_to_response
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

from datazilla.model import DatazillaModel
from datazilla.model import utils

APP_JS = 'application/json'

def graphs(request, project=""):

    ####
    #Load any signals provided in the page
    ####
    signals = []
    time_ranges = utils.get_time_ranges()

    for s in SIGNALS:
        if s in request.POST:
            signals.append( { 'value':urllib.unquote( request.POST[s] ),
                              'name':s } )
    ###
    #Get reference data
    ###
    cache_key = str(project) + '_reference_data'
    json_data = '{}'
    compressed_json_data = cache.get(cache_key)

    time_key = 'days_30'

    ##reference data found in the cache: decompress##
    if compressed_json_data:

        json_data = zlib.decompress( compressed_json_data )

    else:
        ####
        #reference data has not been cached:
        #serialize, compress, and cache
        ####
        dm = DatazillaModel(project)
        ref_data = dm.get_test_reference_data()
        dm.disconnect()

        ref_data['time_ranges'] = time_ranges

        json_data = json.dumps(ref_data)

        cache.set(str(project) + '_reference_data', zlib.compress( json_data ) )

    data = { 'time_key':time_key,
             'reference_json':json_data,
             'signals':signals }

    ####
    #Caller has provided the view parent of the signals, load in page.
    #This occurs when a data view is in its Pane form and is detached
    #to exist on it's own page.
    ####
    parent_index_key = 'dv_parent_dview_index'
    if parent_index_key in request.POST:
        data[parent_index_key] = request.POST[parent_index_key]

    return render_to_response('graphs.views.html', data)


def get_help(request, project=""):
    data = {}
    return render_to_response('help/dataview.generic.help.html', data)


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
    except KeyError as e:
        result = {"status":"No POST data found", "message": e.message}

    unquoted_json_data = urllib.unquote(json_data)

    try:
        json.loads( unquoted_json_data )
    except ValueError as e:
        result = {"status": "Malformed JSON", "message": e.message}

    try:
        dm = DatazillaModel(project)
        dm.store_test_data( unquoted_json_data )
        dm.disconnect()

        status = 200
        result = {
            "status": "well-formed JSON stored",
            "size": str(len(unquoted_json_data)),
            }

    except Exception as e:
        status = 500
        result = {"status":"Unknown error", "message": e.message}

    return HttpResponse(json.dumps(result), mimetype=APP_JS, status=status)


def dataview(request, project="", method=""):

    proc_path = "perftest.views."

    ##Full proc name including base path in json file##
    full_proc_path = "%s%s" % (proc_path, method)

    if settings.DEBUG:
        ###
        #Write IP address and datetime to log
        ###
        print "Client IP:%s" % (request.META['REMOTE_ADDR'])
        print "Request Datetime:%s" % (str(datetime.datetime.now()))

    json = ""
    if method in DATAVIEW_ADAPTERS:
        dm = DatazillaModel(project)
        pt_dhub = dm.sources["perftest"].dhub

        if 'adapter' in DATAVIEW_ADAPTERS[method]:
            json = DATAVIEW_ADAPTERS[method]['adapter'](project,
                                                        method,
                                                        request,
                                                        dm)
        else:
            if 'fields' in DATAVIEW_ADAPTERS[method]:
                fields = []
                for f in DATAVIEW_ADAPTERS[method]['fields']:
                    if f in request.POST:
                        fields.append(
                            pt_dhub.escape_string(request.POST[f]))

                    elif f in request.GET:
                        fields.append(pt_dhub.escape_string(request.GET[f]))

                if len(fields) == len(DATAVIEW_ADAPTERS[method]['fields']):
                    json = pt_dhub.execute(proc=full_proc_path,
                                           debug_show=settings.DEBUG,
                                           placeholders=fields,
                                           return_type='table_json')

                else:
                    json = '{ "error":"%s fields required, %s provided" }' % (str(len(DATAVIEW_ADAPTERS[method]['fields'])),
                                                                              str(len(fields)))

            else:

                json = pt_dhub.execute(proc=full_proc_path,
                                       debug_show=settings.DEBUG,
                                       return_type='table_json')

        dm.disconnect();

    else:
        json = '{ "error":"Data view name %s not recognized" }' % method

    return HttpResponse(json, mimetype=APP_JS)


def _get_test_reference_data(project, method, request, dm):

    ref_data = dm.get_test_reference_data()

    json_data = json.dumps( ref_data )

    return json_data


def _get_test_run_summary(project, method, request, dm):

    product_ids = []
    test_ids = []
    platform_ids = []

    #####
    #Calling get_id_list() insures that we have only numbers in the
    #lists, this gaurds against SQL injection
    #####
    if 'product_ids' in request.GET:
        product_ids = utils.get_id_list(request.GET['product_ids'])
    if 'test_ids' in request.GET:
        test_ids = utils.get_id_list(request.GET['test_ids'])
    if 'platform_ids' in request.GET:
        platform_ids = utils.get_id_list(request.GET['platform_ids'])

    time_key = 'days_30'
    time_ranges = utils.get_time_ranges()
    if 'tkey' in request.GET:
        time_key = request.GET['tkey']

    if not product_ids:
        ##Set default product_id##
        product_ids = [12]

    json_data = '{}'

    if product_ids and (not test_ids) and (not platform_ids):

        if len(product_ids) > 1:
            extend_list = { 'data':[], 'columns':[] }
            for id in product_ids:
                key = utils.get_cache_key(project, str(id), time_key)
                compressed_json_data = cache.get(key)

                if compressed_json_data:
                    json_data = zlib.decompress( compressed_json_data )
                    data = json.loads( json_data )
                    extend_list['data'].extend( data['data'] )
                    extend_list['columns'] = data['columns']

            json_data = json.dumps(extend_list)

        else:
            key = utils.get_cache_key(
                project,
                str(product_ids[0]),
                time_key,
                )
            compressed_json_data = cache.get(key)

            if compressed_json_data:
                json_data = zlib.decompress( compressed_json_data )

    else:
        table = dm.get_test_run_summary(time_ranges[time_key]['start'],
                                     time_ranges[time_key]['stop'],
                                     product_ids,
                                     platform_ids,
                                     test_ids)

        json_data = json.dumps( table )

    return json_data


def _get_test_values(project, method, request, dm):

    data = {};

    if 'test_run_id' in request.GET:
        data = dm.get_test_run_values( request.GET['test_run_id'] )

    json_data = json.dumps( data )

    return json_data


def _get_page_values(project, method, request, dm):

    data = {};

    if ('test_run_id' in request.GET) and ('page_id' in request.GET):
        data = dm.get_page_values( request.GET['test_run_id'], request.GET['page_id'] )

    json_data = json.dumps( data )

    return json_data


def _get_test_value_summary(project, method, request, dm):

    data = {};

    if 'test_run_id' in request.GET:
        data = dm.get_test_run_value_summary( request.GET['test_run_id'] )

    json_data = json.dumps( data )

    return json_data


#####
#UTILITY METHODS
#####
DATAVIEW_ADAPTERS = { ##Flat tables SQL##
                      'test_run':{},
                      'test_value':{ 'fields':[ 'test_run_id', ] },
                      'test_option_values':{ 'fields':[ 'test_run_id', ] },
                      'test_aux_data':{ 'fields':[ 'test_run_id', ] },

                      ##API only##
                      'get_test_ref_data':{ 'adapter':_get_test_reference_data},

                      ##Visualization Tools##
                      'test_runs':{ 'adapter':_get_test_run_summary,
                                    'fields':['test_run_id',
                                              'test_run_data']
                                  },

                      'test_chart':{ 'adapter':_get_test_run_summary,
                                     'fields':['test_run_id',
                                               'test_run_data'] },

                      'test_values':{ 'adapter':_get_test_values,
                                      'fields':['test_run_id'] },

                      'page_values':{ 'adapter':_get_page_values,
                                      'fields':['test_run_id',
                                                'page_id'] },

                      'test_value_summary':{ 'adapter':_get_test_value_summary,
                                             'fields':['test_run_id'] } }

SIGNALS = set()
for dv in DATAVIEW_ADAPTERS:
    if 'fields' in DATAVIEW_ADAPTERS[dv]:
        for field in DATAVIEW_ADAPTERS[dv]['fields']:
            SIGNALS.add(field)
