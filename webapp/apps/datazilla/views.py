import os
import datetime
import json
import urllib
import datetime
import time
import zlib

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render_to_response
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, HttpResponseServerError, HttpResponseBadRequest, HttpResponseForbidden
import memcache

from datazilla.model.DatazillaModel import DatazillaModel

APP_JS = 'application/json'

def graphs(request):

   ####
   #Load any signals provided in the page
   ####
   signals = []
   startDate, endDate = _getDateRange()

   for s in SIGNALS:
     if s in request.POST:
        if s == 'start_date':
           startDate = datetime.date( *time.strptime(request.POST[s], '%Y-%m-%d')[0:3] )
        elif s == 'end_date':
           endDate = datetime.date( *time.strptime(request.POST[s], '%Y-%m-%d')[0:3] )
        else:
           signals.append( { 'value':urllib.unquote( request.POST[s] ), 'name':s } )

   ###
   #Get reference data
   ###
   cacheKey = 'reference_data'
   jsonData = '{}'
   mc = memcache.Client([settings.DATAZILLA_MEMCACHED], debug=0)
   compressedJsonData = mc.get(cacheKey)

   ##reference data found in the cache: decompress##
   if compressedJsonData:
      jsonData = zlib.decompress( compressedJsonData )
   else:
      ##reference data has not been cached: serialize, compress, and cache##
      gm = DatazillaModel('graphs.json')
      refData = gm.getTestReferenceData()
      gm.disconnect()

      jsonData = json.dumps(refData)

      mc.set('reference_data', zlib.compress( jsonData ) )

   data = { 'username':request.user.username,
            'start_date':startDate,
            'end_date':endDate,
            'reference_json':jsonData,
            'current_date':datetime.date.today(),
            'signals':signals }

   ####
   #Caller has provided the view parent of the signals, load in page.
   #This occurs when a data view is in its Pane form and is detached
   #to exist on it's own page.
   ####
   parentIndexKey = 'dv_parent_dview_index'
   if parentIndexKey in request.POST:
     data[parentIndexKey] = request.POST[parentIndexKey]

   return render_to_response('graphs.views.html', data)

def getHelp(request):
   data = {}
   return render_to_response('help/dataview.generic.help.html', data)

def getDateRange(request):

   start_date, end_date = _getDateRange()

   current_date = datetime.date.today()

   jsonData = json.dumps( { 'start_date':str(start_date),
                            'end_date':str(end_date),
                            'current_date':str(current_date) } )

   return HttpResponse(jsonData, mimetype=APP_JS)

def setTestData(procPath, procName, fullProcPath, request, gm):

   jsonData = '{"error":"No POST data found"}'

   if 'data' in request.POST:

      jsonData = request.POST['data']
      unquotedJsonData = urllib.unquote(jsonData)
      data = json.loads( unquotedJsonData )
      gm = DatazillaModel('graphs.json')
      gm.loadTestData( data, unquotedJsonData )
      jsonData = json.dumps( { 'loaded_test_pages':len(data['results']) } )

   return jsonData

def dataview(request, **kwargs):

   procName = os.path.basename(request.path)
   procPath = "graphs.views."
   ##Full proc name including base path in json file##
   fullProcPath = "%s%s" % (procPath, procName)

   if settings.DEBUG:
      ###
      #Write IP address and datetime to log
      ###
      print "Client IP:%s" % (request.META['REMOTE_ADDR'])
      print "Request Datetime:%s" % (str(datetime.datetime.now()))

   json = ""
   if procName in DATAVIEW_ADAPTERS:
      gm = DatazillaModel('graphs.json')
      if 'adapter' in DATAVIEW_ADAPTERS[procName]:
         json = DATAVIEW_ADAPTERS[procName]['adapter'](procPath, 
                                                       procName, 
                                                       fullProcPath, 
                                                       request,
                                                       gm)
      else:
         if 'fields' in DATAVIEW_ADAPTERS[procName]:
            fields = []
            for f in DATAVIEW_ADAPTERS[procName]['fields']:
               if f in request.POST:
                  fields.append( gm.dhub.escapeString( request.POST[f] ) )
               elif f in request.GET:
                  fields.append( gm.dhub.escapeString( request.GET[f] ) )

            if len(fields) == len(DATAVIEW_ADAPTERS[procName]['fields']):
               json = gm.dhub.execute(proc=fullProcPath,
                                      debug_show=settings.DEBUG,
                                      placeholders=fields,
                                      return_type='table_json')

            else:
               json = '{ "error":"%s fields required, %s provided" }' % (str(len(DATAVIEW_ADAPTERS[procName]['fields'])), 
                                                                         str(len(fields)))

         else:

            json = gm.dhub.execute(proc=fullProcPath,
                                   debug_show=settings.DEBUG,
                                   return_type='table_json')

   else:
      json = '{ "error":"Data view name %s not recognized" }' % procName

   gm.disconnect();

   return HttpResponse(json, mimetype=APP_JS)

def _getTestReferenceData(procPath, procName, fullProcPath, request, gm):

   refData = gm.getTestReferenceData()

   jsonData = json.dumps( refData )

   return jsonData


def _getTestRunSummary(procPath, procName, fullProcPath, request, gm):

   productIds = [] 
   testIds = [] 
   platformIds = []

   #####
   #Calling _getIdList() insures that we have only numbers in the 
   #lists, this gaurds against SQL injection
   #####
   if 'product_ids' in request.GET:
      productIds = DatazillaModel.getIdList(request.GET['product_ids'])
   if 'test_ids' in request.GET:
      testIds = DatazillaModel.getIdList(request.GET['test_ids'])
   if 'platform_ids' in request.GET:
      platformIds = DatazillaModel.getIdList(request.GET['platform_ids'])

   if not productIds:
      ##Set default productId##
      productIds = [12]

   jsonData = '{}'
   timeKey = 'days_7'
   timeRanges = DatazillaModel.getTimeRanges()

   mc = memcache.Client([settings.DATAZILLA_MEMCACHED], debug=0)

   if productIds and (not testIds) and (not platformIds):

      if len(productIds) > 1:
         extendList = { 'data':[], 'columns':[] } 
         for id in productIds:
            key = DatazillaModel.getCacheKey(str(id), timeKey)
            compressedJsonData = mc.get(key)
            if compressedJsonData:
               jsonData = zlib.decompress( compressedJsonData )
               data = json.loads( jsonData )
               extendList['data'].extend( data['data'] )
               extendList['columns'] = data['columns']

         jsonData = json.dumps(extendList)

      else:
         key = DatazillaModel.getCacheKey(str(productIds[0]), timeKey)
         compressedJsonData = mc.get(key)

         if compressedJsonData:
            jsonData = zlib.decompress( compressedJsonData )

   else:
      table = gm.getTestRunSummary(timeRanges[timeKey]['start'], 
                                   timeRanges[timeKey]['stop'], 
                                   productIds, 
                                   platformIds, 
                                   testIds)

      jsonData = json.dumps( table )

   return jsonData

def _getTestValues(procPath, procName, fullProcPath, request, gm):

   data = {};

   if 'test_run_id' in request.GET:
      data = gm.getTestRunValues( request.GET['test_run_id'] )

   jsonData = json.dumps( data )

   return jsonData

def _getPageValues(procPath, procName, fullProcPath, request, gm):

   data = {};

   if ('test_run_id' in request.GET) and ('page_id' in request.GET):
      data = gm.getPageValues( request.GET['test_run_id'], request.GET['page_id'] )

   jsonData = json.dumps( data )

   return jsonData


def _getTestValueSummary(procPath, procName, fullProcPath, request, gm):

   data = {};

   if 'test_run_id' in request.GET:
      data = gm.getTestRunValueSummary( request.GET['test_run_id'] )

   jsonData = json.dumps( data )

   return jsonData

#####
#UTILITY METHODS
#####
def _getDateRange():

   start_date = datetime.date.today() - datetime.timedelta(hours=24)
   end_date = datetime.date.today() + datetime.timedelta(hours=24)

   return start_date, end_date

DATAVIEW_ADAPTERS = { ##Flat tables SQL##
                      'test_run':{},
                      'test_value':{ 'fields':[ 'test_run_id', ] },
                      'test_option_values':{ 'fields':[ 'test_run_id', ] },
                      'test_aux_data':{ 'fields':[ 'test_run_id', ] },

                      ##API only##
                      'get_test_ref_data':{ 'adapter':_getTestReferenceData},

                      ##Visualization Tools##
                      'test_runs':{ 'adapter':_getTestRunSummary, 'fields':['test_run_id', 'test_run_data'] },

                      'test_chart':{ 'adapter':_getTestRunSummary, 'fields':['test_run_id', 'test_run_data'] },
                      
                      'test_values':{ 'adapter':_getTestValues, 'fields':['test_run_id'] }, 

                      'page_values':{ 'adapter':_getPageValues, 'fields':['test_run_id', 'page_id'] }, 

                      'test_value_summary':{ 'adapter':_getTestValueSummary, 'fields':['test_run_id'] } }

SIGNALS = set()
for dv in DATAVIEW_ADAPTERS:
   if 'fields' in DATAVIEW_ADAPTERS[dv]:
      for field in DATAVIEW_ADAPTERS[dv]['fields']:
         SIGNALS.add(field)

