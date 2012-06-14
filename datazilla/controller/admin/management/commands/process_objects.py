import os
import json

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import DatazillaModel

class Command(BaseCommand):

    help = "Transfer json blobs from the key/value store, uncompacting" \
            "them appropriately to the appropriate database."

    option_list = BaseCommand.option_list + (
        make_option('--project',
                    action='store',
                    dest='project',
                    default=False,
                    help='Source project to pull data from: talos, ' +
                         'b2g, stoneridge, test etc...'),
        make_option('--loadlimit',
                    action='store',
                    dest='loadlimit',
                    default=1,
                    help='Number of JSON blobs to fetch per '+
                         'single iteration of uncompacting'),
        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=None,
                    help='Write json-encapsulated SQL query out for debugging'))


    def handle(self, *args, **options):

        project   = options.get('project')
        debug     = options.get('debug')
        loadlimit = options.get('loadlimit')

        if not loadlimit:
            loadlimit = 1

        if not project:
            print "ERROR: Enter a valid project name"
            quit()


        dm = DatazillaModel(project)

        """
        Note: this is a locking retrieval. Failure
        to call load_test_data on this data will result
        in some loads of json being stuck in limbo,
        which merits creating a cleanup utility.
        """
        json_blobs = dm.retrieve_test_data(loadlimit, lock_rows=True)

        for json_blob in json_blobs:

            ## Print only if debug, otherwise load into perftest db ##
            if options['debug']:
                self.stdout.write(str(json_blob['json_blob'])+'\n')
            else:
                """
                TODO: Implement some sort of verification
                json is well-formed to ensure load_test_data
                won't fail.
                """
                dm.load_test_data(json_blob, call_completed=True)

        dm.disconnect()
