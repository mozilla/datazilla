import os

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import PerformanceTestModel

class Command(BaseCommand):

    help = (
            "Transfer json blobs from the key/value store, uncompacting"
            "them appropriately to the appropriate database."
            )

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
                    help='Number of JSON blobs to fetch per '
                         'single iteration of uncompacting'),
        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=None,
                    help='Write json-encapsulated SQL query out for debugging'))


    def handle(self, *args, **options):

        project   = options.get('project')
        debug     = options.get('debug')

        loadlimit = int(options.get("loadlimit", 1))

        if not project:
            raise CommandError("Enter a valid project name")

        dm = PerformanceTestModel(project)
        dm.process_objects(loadlimit)
        dm.disconnect()
