from optparse import make_option


from datazilla.controller.admin import collection
from django.core.management.base import NoArgsCommand
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
        project = self._get_required_project(options)

        if options.get("load"):
            collection.load_test_collection(project)
