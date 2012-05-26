from datazilla.vendor import add_vendor_lib
add_vendor_lib()

import os
import sys
import json
import memcache
import zlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")
from django.conf import settings

from django.conf import settings
from optparse import OptionParser
from datazilla.model.DatazillaModel import DatazillaModel

"""
This script builds the test run summary data structure for
a 7 and 30 day period interval for every product/branch/version.

These data structures are stored in the summary_cache table.  They
need to persist if the memcache goes down, they take several minutes
to generate.  As the quantity of data grows this will likely take
significantly longer.
"""

def cacheTestSummaries(project):

    gm = DatazillaModel(project, 'graphs.json')
    dataIter = gm.getAllSummaryCache()

    mc = memcache.Client([settings.DATAZILLA_MEMCACHED], debug=0)

    for d in dataIter:
        for data in d:
            key = DatazillaModel.getCacheKey( project,
                                              data['item_id'],
                                              data['item_data'] )

            rv = mc.set(key, zlib.compress( data['value'] ))
            if not rv:
                sys.stderr.write("ERROR: Failed to store object in memcache: %s, %s\n" % ( str(data['item_id']), data['item_data'] ) )

    gm.disconnect()

def buildTestSummaries(project):

    gm = DatazillaModel(project, 'graphs.json')

    timeRanges = DatazillaModel.getTimeRanges()

    products = gm.getProducts()

    for productName in products:

        for tr in ['days_7', 'days_30']:

            table = gm.getTestRunSummary(str( timeRanges[tr]['start']),
                                         str( timeRanges[tr]['stop']),
                                         [ products[ productName ] ],
                                         [],
                                         [])

            jsonData = json.dumps( table )

            gm.setSummaryCache( products[ productName ], tr, jsonData )

    gm.disconnect()

if __name__ == '__main__':

    usage = """usage: %prog [options] --project project_name --build --cache --verbose"""
    parser = OptionParser(usage=usage)

    parser.add_option('-p',
                      '--project',
                      action='store',
                      dest='project',
                      default=False,
                      type='string',
                      help="Set the project to run on: talos, " +
                           "b2g, schema, test etc....")

    parser.add_option('-b',
                      '--build',
                      action='store_true',
                      dest='build',
                      default=False,
                      type=None,
                      help="Build the test run summaries and " +
                           "store them in the database.")

    parser.add_option('-c',
                      '--cache',
                      action='store_true',
                      dest='cache',
                      default=False,
                      type=None,
                      help="Update the test run summaries in memcached")

    (options, args) = parser.parse_args()

    if not options.project:
        print "No project argument provided."
        print parser.usage
        sys.exit(0)

    if options.build:
        buildTestSummaries(options.project)

    if options.cache:
        cacheTestSummaries(options.project)
