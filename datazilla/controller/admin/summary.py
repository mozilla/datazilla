"""
Functions for populating summary cache.

@@@ Should these just be methods on DatazillaModel instead?

"""
import json
import zlib
import sys

from datazilla.model import DatazillaModel, utils
from django.core.cache import cache



def cache_test_summaries(project):

    dm = DatazillaModel(project)
    data_iter = dm.get_all_summary_cache()

    for d in data_iter:
        for data in d:
            key = utils.get_cache_key(
                project,
                data['item_id'],
                data['item_data'],
                )

            rv = cache.set(key, zlib.compress( data['value'] ))
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
