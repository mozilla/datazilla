import time

from datetime import timedelta
from optparse import make_option

from datazilla.model import MetricsTestModel, PushLogModel
from base import ProjectBatchCommand

class Command(ProjectBatchCommand):
    LOCK_FILE = "backfill_all_dimensions"

    help = "Backfill the test_data_all_dimensions table"

    option_list = ProjectBatchCommand.option_list + (

        make_option(
            '--numdays',
            action='store',
            dest='numdays',
            default=1,
            help='Number of days ago to start the backfill from'),
            )


    def handle_project(self, project, **options):

        def to_seconds(td):
            return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

        numdays = int(options.get("numdays", 1))
        now = int(time.time())
        time_constraint = now - to_seconds(timedelta(numdays))

        mtm = MetricsTestModel(project)

        test_run_ids = mtm.get_test_runs_not_in_all_dimensions(time_constraint)
        self.stdout.write("test run ids {0}\n".format(str(len(test_run_ids))))

        #Make a list of test_run_id chunks to iterate over
        chunk_size = 20
        test_run_id_chunks = [
            test_run_ids[i:i + chunk_size] for i in range(0, len(test_run_ids), chunk_size)
            ]

        plm = PushLogModel()

        for ids in test_run_id_chunks:

            self.stdout.write("Processing ids {0}\n".format(str(ids)))

            revisions_without_push_data = mtm.load_test_data_all_dimensions(ids)

            if revisions_without_push_data:

                revision_nodes = {}

                for revision in revisions_without_push_data:

                    node = plm.get_node_from_revision(
                        revision, revisions_without_push_data[revision])

                    revision_nodes[revision] = node

                mtm.set_push_data_all_dimensions(revision_nodes)

        plm.disconnect()
        mtm.disconnect()

