from optparse import make_option

from datazilla.model import PerformanceTestModel, MetricsTestModel, PushLogModel
from base import ProjectBatchCommand

from datazilla.controller.admin.metrics.perftest_metrics import compute_test_run_metrics

class Command(ProjectBatchCommand):
    LOCK_FILE = "process_objects"

    help = (
            "Transfer json blobs from the key/value store, uncompacting"
            "them appropriately to the appropriate database, and run "
            "metrics."
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

        make_option(
            '--pushlog_project',
            action='store',
            dest='pushlog_project',
            default=None,
            help="Push log project name (defaults to pushlog)"),

        )


    def handle_project(self, project, **options):

        self.stdout.write("Processing project {0}\n".format(project))

        pushlog_project = options.get("pushlog_project", 'pushlog')
        loadlimit = int(options.get("loadlimit", 1))
        debug = options.get("debug", None)

        test_run_ids = []
        ptm = PerformanceTestModel(project)
        test_run_ids = ptm.process_objects(loadlimit)
        ptm.disconnect()

        metrics_exclude_projects = set(['b2g', 'games', 'jetperf', 'marketapps', 'microperf', 'stoneridge', 'test', 'webpagetest'])

        if project not in metrics_exclude_projects:
            #minimum required number of replicates for
            #metrics processing
            replicate_min = 5
            compute_test_run_metrics(
                project, pushlog_project, debug, replicate_min, test_run_ids
                )

        mtm = MetricsTestModel(project)
        revisions_without_push_data = mtm.load_test_data_all_dimensions(
            test_run_ids)

        if revisions_without_push_data:

            revision_nodes = {}
            plm = PushLogModel(pushlog_project)

            for revision in revisions_without_push_data:

                node = plm.get_node_from_revision(
                    revision, revisions_without_push_data[revision])

                revision_nodes[revision] = node

            plm.disconnect()
            mtm.set_push_data_all_dimensions(revision_nodes)

        mtm.disconnect()


