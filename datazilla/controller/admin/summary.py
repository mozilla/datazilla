"""
Functions for populating summary cache.

"""
import json
import zlib
import sys

from datazilla.model import PerformanceTestModel, utils
from django.core.cache import cache



def cache_test_summaries(project):

    ptm = PerformanceTestModel(project)

    ###
    #New reference data could be found in the cached data
    #summary structures. Update the reference data cached 
    #every time the sumary data is cached.
    ###
    ptm.cache_ref_data()
    ptm.cache_default_project()

    data_iter = ptm.get_all_summary_cache()

    key_test = []
    for d in data_iter:
        for data in d:
            key = utils.get_summary_cache_key(
                project,
                data['item_id'],
                data['item_data'],
                )
            rv = cache.set(key, zlib.compress( data['value'] ))
            if not rv:
                msg = "ERROR: Failed to store object in memcache: %s, %s\n" % \
                        ( str(data['item_id']), data['item_data'] )
                sys.stderr.write(msg)

    ptm.disconnect()



def build_test_summaries(project):

    ptm = PerformanceTestModel(project)

    time_ranges = utils.get_time_ranges()

    products = ptm.get_products()

    for product_name in products:

        for tr in ['days_7', 'days_30']:

            table = ptm.get_test_run_summary(str( time_ranges[tr]['start']),
                                         str( time_ranges[tr]['stop']),
                                         [ products[ product_name ] ],
                                         [],
                                         [])

            json_data = json.dumps( table )
            ptm.set_summary_cache( products[ product_name ], tr, json_data )

    ptm.disconnect()
