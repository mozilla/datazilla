from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import PushLogModel

class Command(BaseCommand):
    """Management command to create the pushlog database for known repos."""

    help = "Create all databases for the pushlogs."

    option_list = BaseCommand.option_list + (
        make_option('--host',
                    action='store',
                    dest='host',
                    default=None,
                    help='The host name for the database'),

        make_option('--type',
                    action='store',
                    dest='type',
                    default=None,
                    help='The database type (e.g. "MySQL-InnoDB") '
                         'for the database'),)

    def handle(self, *args, **options):
        """ Create databases for a new project based on the args value. """

        pl = PushLogModel.create(
            host=options.get("host"),
            type=options.get("type"),
            )
        pl.disconnect()
