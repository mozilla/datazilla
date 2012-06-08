"""
This script builds the test run summary data structure for
a 7 and 30 day period interval for every product/branch/version.

These data structures are stored in the summary_cache table.  They
need to persist if the memcache goes down, they take several minutes
to generate.  As the quantity of data grows this will likely take
significantly longer.

"""

from datazilla.vendor import add_vendor_lib
add_vendor_lib()

import os
import sys
import json
import memcache
import zlib

from optparse import OptionParser
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datazilla.settings.base")

from django.conf import settings
from datazilla.model import DatazillaModel
from datazilla.model import utils
from django.core.cache import cache


def cache_test_summaries(project):

    dm = DatazillaModel(project)
    data_iter = dm.get_all_summary_cache()

    mc = memcache.Client([settings.DATAZILLA_MEMCACHED], debug=0)

    for d in data_iter:
        for data in d:
            key = utils.get_cache_key(
                project,
                data['item_id'],
                data['item_data'],
                )

            rv = mc.set(key, zlib.compress( data['value'] ))
            if not rv:
                msg = "ERROR: Failed to store object in memcache: %s, %s\n" % \
                        ( str(data['item_id']), data['item_data'] ) 
                sys.stderr.write(msg)

    dm.disconnect()

def build_test_summaries(project):

    dm = DatazillaModel(project)

    time_ranges = utils.get_time_ranges()

    products = dm.get_products()

    for product_name in products:

        for tr in ['days_7', 'days_30']:

            table = dm.get_test_run_summary(str( time_ranges[tr]['start']),
                                         str( time_ranges[tr]['stop']),
                                         [ products[ product_name ] ],
                                         [],
                                         [])

            json_data = json.dumps( table )

            dm.set_summary_cache( products[ product_name ], tr, json_data )

    dm.disconnect()

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
        build_test_summaries(options.project)

    if options.cache:
        cache_test_summaries(options.project)
