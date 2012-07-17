from optparse import make_option


from datazilla.controller.admin import collection
from django.core.management.base import NoArgsCommand, CommandError
from base import ProjectCommandBase



class Command(ProjectCommandBase):
    help = "Populate test collections."

    option_list = NoArgsCommand.option_list + (

        make_option(
            '-l',
            '--load',
            action='store_true',
            dest='load',
            default=False,
            type=None,
            help=(
                "Identify new product branches "
                "and add them as test collections."
                ),
            ),
        )


    def handle_noargs(self, **options):
        project = options.get("project")
        if not project:
            raise CommandError("No project argument provided.")

        if options.get("load"):
            collection.load_test_collection(project)
