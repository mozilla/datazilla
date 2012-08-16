#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
"""
Model-layer utility functions.

"""
import time
import datetime



def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_id_string(id_list):
    """Return given list formatted as comma-separated string."""
    return ",".join(map(str, id_list))


def get_id_list(id_string):
    """
    Split comma-separated string and cast each element to int.

    If any element can't be cast to an integer, returns an empty list.

    """
    try:
        return map(int, id_string.split(",") )
    except ValueError:
        ##Cast to int failed, must not be a number##
        return []


def get_summary_cache_key(project, item_id, item_data):
    """Return a cache key for given project, item id, and data."""
    return "_".join(map(str, [project, item_id, item_data]))


def get_day_range(days_ago, numdays=None):
    """Return a start and stop date based on values given in unix timestamp"""

    # if numdays not given, get all since days_ago (same value)
    numdays = numdays or days_ago

    from datetime import timedelta
    def to_seconds(td):
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    now = int(time.time())
    start = now - to_seconds(timedelta(int(days_ago)))
    stop = start + to_seconds(timedelta(int(numdays)))
    return {"start": int(start), "stop": int(stop)}


def get_time_ranges():
    """
    Get a dictionary of time ranges.

    """
    #############
    #  time.time() is used to generate the unix timestamp
    #  associated with the json structure pushed to the database
    #  by a talos bot.  So all time ranges need to be computed in
    #  seconds since the epoch
    ############

    now = int(time.time())

    time_ranges = {
        'days_7': { 'start': now, 'stop': now - 604800 },
        'days_30': { 'start': now, 'stop': now - 2592000 },
        #'days_60': { 'start': now, 'stop': now - 5184000 },
        #'days_90': { 'start': now, 'stop': now - 7776000 },
        #'days_360': { 'start':now, 'stop':now - 31557600 },
        }
    ###
    #Add a readable version of start/stop for each time range
    ###
    # @@@ Should do this in the display layer, not the model layer
    for data in time_ranges.values():
        date_format = '%Y-%m-%d'
        data["rstart"] = datetime.datetime.fromtimestamp(
            data["start"]).strftime(date_format)
        data["rstop"] = datetime.datetime.fromtimestamp(
            data["stop"]).strftime(date_format)

    return time_ranges


def build_replacement(col_data):
    return "AND " + " AND ".join(
        [
            "%s IN (%s)" % (key, value)
            for key, value in col_data.items()
            if value
            ]
        )
