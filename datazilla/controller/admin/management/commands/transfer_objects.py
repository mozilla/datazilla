import os

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import DatazillaModel

class Command(BaseCommand):

    help = (
            "Transfer objects from the old test_data store to the objectstore "
            "for a project."
            )

    option_list = BaseCommand.option_list + (
        make_option('--project',
                    action='store',
                    dest='project',
                    default=False,
                    help='Source project to pull data from: talos, ' +
                         'b2g, stoneridge, test etc...'),
        make_option('--limit',
                    action='store',
                    dest='limit',
                    default=1,
                    help='Number of JSON blobs to fetch from test_data during '
                         'this call.'),
        make_option('--start',
                    action='store',
                    dest='start',
                    default=1,
                    help='ID of row to start transferring from'),
        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=False,
                    help='Write SQL query out for debugging'))


    def handle(self, *args, **options):

        project   = options.get('project')
        debug     = options.get('debug')

        limit = int(options.get("limit", 1))
        start = int(options.get("start", 1))

        if not project:
            raise CommandError("Enter a valid project name")

        dm = DatazillaModel(project)
        dm.transfer_objects(start, limit)
        dm.disconnect()
