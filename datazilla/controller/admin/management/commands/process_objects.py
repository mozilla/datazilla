from optparse import make_option

from datazilla.model import PerformanceTestModel
from base import ProjectBatchCommand

class Command(ProjectBatchCommand):
    LOCK_FILE = "process_objects"

    help = (
            "Transfer json blobs from the key/value store, uncompacting"
            "them appropriately to the appropriate database."
            )

    option_list = ProjectBatchCommand.option_list + (

        make_option(
            '--loadlimit',
            action='store',
            dest='loadlimit',
            default=1,
            help='Number of JSON blobs to fetch per '
                 'single iteration of uncompacting'),

        make_option(
            '--debug',
            action='store_true',
            dest='debug',
            default=None,
            help='Write json-encapsulated SQL query out for debugging'),

        )


    def handle_project(self, project, options):
        self.stdout.write("Processing project {0}\n".format(project))

        loadlimit = int(options.get("loadlimit", 1))

        dm = PerformanceTestModel(project)
        dm.process_objects(loadlimit)
        dm.disconnect()
