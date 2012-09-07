from optparse import make_option


from datazilla.controller.admin import collection
from base import ProjectBatchCommand



class Command(ProjectBatchCommand):
    help = "Populate test collections."

    option_list = ProjectBatchCommand.option_list + (

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


    def handle_project(self, project, **options):
        self.stdout.write("Processing project {0}\n".format(project))

        if options.get("load"):
            collection.load_test_collection(project)
