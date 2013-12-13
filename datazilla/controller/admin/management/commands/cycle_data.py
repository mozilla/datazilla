from optparse import make_option

from datazilla.model import PerformanceTestModel
from base import ProjectBatchCommand

from datazilla.controller.admin.metrics.perftest_metrics import compute_test_run_metrics

class Command(ProjectBatchCommand):
    LOCK_FILE = "cycle_data"

    help = (
            "Delete data older than 6 months in all perftest schemas."
            )

    option_list = ProjectBatchCommand.option_list + (

        make_option(
            '--debug',
            action='store_true',
            dest='debug',
            default=None,
            help='Write json-encapsulated SQL query out for debugging'),

        )


    def handle_project(self, project, **options):

        debug = options.get("debug", None)

        ptm = PerformanceTestModel(project)
        ptm.cycle_data()
        ptm.disconnect()

