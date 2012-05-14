import os
import sys
import time
import datetime
import json
import memcache
import zlib

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

def cacheTestSummaries():

    gm = DatazillaModel('graphs.json')
    dataIter = gm.getAllSummaryCache()

    mc = memcache.Client([os.environ["DATAZILLA_MEMCACHED"]], debug=0)

    for d in dataIter:
        for data in d:
            key = DatazillaModel.getCacheKey( data['item_id'], data['item_data'] )
            rv = mc.set(key, zlib.compress( data['value'] ))
            if not rv:
                sys.stderr.write("ERROR: Failed to store object in memcache: %s, %s\n" % ( str(data['item_id']), data['item_data'] ) )

    gm.disconnect()

def buildTestSummaries():

    gm = DatazillaModel('graphs.json')

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

    usage = """usage: %prog [options] --build --cache --verbose"""
    parser = OptionParser(usage=usage)

    parser.add_option('-b',
                      '--build',
                      action='store_true',
                      dest='build',
                      default=False,
                      type=None,
                      help="Build the test run summaries and store them in the database.")

    parser.add_option('-c',
                      '--cache',
                      action='store_true',
                      dest='cache',
                      default=False,
                      type=None,
                      help="Update the test run summaries in memcached")

    (options, args) = parser.parse_args()

    if options.build:
        buildTestSummaries()

    if options.cache:
        cacheTestSummaries()
