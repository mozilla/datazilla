from optparse import make_option

from datazilla.model import PerformanceTestModel
from base import ProjectBatchCommand

from datazilla.controller.admin.metrics.perftest_metrics import compute_test_run_metrics

class Command(ProjectBatchCommand):
    LOCK_FILE = "cycle_data"

    help = (
            "Delete data older than 6 months in appropriate objectstore and perftest schemas."
            )

    option_list = ProjectBatchCommand.option_list + (

        make_option(
            '--debug',
            action='store_true',
            dest='debug',
            default=None,
            help='Write json-encapsulated SQL query out for debugging'),

        make_option(
            '--iterations',
            action='store',
            dest='iterations',
            default=50,
            help='Number of delete iterations to do in one run '),
        )

    def handle_project(self, project, **options):

        debug = options.get("debug", None)
        max_iterations = int(options.get("iterations", 50))

        ptm = PerformanceTestModel(project)


        sql_targets = {}

        while max_iterations > 0:

            sql_targets = ptm.cycle_data(sql_targets)

            # No more items to delete
            if not sql_targets:
                break

            max_iterations -= 1

            if debug:
                print "Iterations: {0}".format(str(max_iterations))
                print "sql_targets"
                print sql_targets

        ptm.disconnect()

