
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import DatazillaModel

class Command(BaseCommand):

    help = "Create all necessary tables for a new project."

    def handle(self, *args, **options):
        """ Create tables for a new project based on the args value. """

        try:
            project_name = args[0]
            dm = DatazillaModel.create(project_name)
            dm.disconnect()

        except IndexError as e:
            self.stdout.write("You must supply the name of the new project\n")
