from optparse import make_option


from datazilla.controller.admin import collection
from base import ProjectBatchCommandBase



class Command(ProjectBatchCommandBase):
    help = "Populate test collections."

    option_list = ProjectBatchCommandBase.option_list + (

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


    def handle_one_project(self, project, options):
        self.stdout.write("Processing project {0}\n".format(project))

        if options.get("load"):
            collection.load_test_collection(project)
