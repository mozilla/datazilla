from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import DatazillaModel

class Command(BaseCommand):
    """Management command to create all databases for a new project."""

    help = "Create all databases for a new project."

    option_list = BaseCommand.option_list + (
        make_option('--project',
                    action='store',
                    dest='project',
                    default=None,
                    help='Project identifier: talos, ' +
                         'b2g, stoneridge, test etc...'),

        make_option('--perftest_host',
                    action='store',
                    dest='perftest_host',
                    default=None,
                    help='The host name for the perftest database'),

        make_option('--objectstore_host',
                    action='store',
                    dest='objectstore_host',
                    default=None,
                    help='The host name for the objectstore database'),

        make_option('--perftest_type',
                    action='store',
                    dest='perftest_type',
                    default=None,
                    help='The database type (e.g. "MySQL-InnoDB") '
                    'for the perftest database'),

        make_option('--objectstore_type',
                    action='store',
                    dest='objectstore_type',
                    default=None,
                    help='The database type (e.g. "MySQL-Aria") '
                    'for the objectstore database'),)

    def handle(self, *args, **options):
        """ Create databases for a new project based on the args value. """

        project = options.get('project')

        if not project:
            self.stdout.write("You must supply a project name " +
                              "to create: --project project\n")
            return

        hosts = dict(
            perftest=options.get("perftest_host"),
            objectstore=options.get("objectstore_host"),
            )

        types = dict(
            perftest=options.get("perftest_type"),
            objectstore=options.get("objectstore_type"),
            )

        dm = DatazillaModel.create(project, hosts=hosts, types=types)

        dm.disconnect()
