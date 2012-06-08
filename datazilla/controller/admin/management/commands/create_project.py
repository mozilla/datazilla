from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import DatazillaModel

class Command(BaseCommand):
    """Management command to Create all necessary tables for a new project."""

    help = "Create all necessary tables for a new project."

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
                    help='The host name for the objectstore database'),)

    def handle(self, *args, **options):
        """ Create tables for a new project based on the args value. """

        project = options.get('project')
        perftest_host = options.get('perftest_host')
        objectstore_host = options.get('objectstore_host')

        if not project:
            self.stdout.write("You must supply a project name " +
                              "to create: --project project\n")

        if not perftest_host:
            self.stdout.write("You must supply the host name of the " +
                              "perftest database: --perftest_host " +
                              "hostname\n")

        if not objectstore_host:
            self.stdout.write("You must supply the host name of the " +
                              "objectstore database: --objectstore_host " +
                              "hostname\n")

        hosts = dict(perftest=perftest_host,
                     objectstore=objectstore_host)

        dm = DatazillaModel.create(project, hosts)

        dm.disconnect()
