"""
This script builds the test run summary data structure for
a 7 and 30 day period interval for every product/branch/version.

These data structures are stored in the summary_cache table.  They
need to persist if the memcache goes down, they take several minutes
to generate.  As the quantity of data grows this will likely take
significantly longer.

"""
from optparse import make_option

from datazilla.controller.admin import push_walker
from base import ProjectBatchCommand


class Command(ProjectBatchCommand):

    LOCK_FILE = "run_metrics"

    help = "Populate the summary cache for a project."

    option_list = ProjectBatchCommand.option_list + (

        make_option(
            '-b',
            '--bootstrap',
            action='store_true',
            dest='bootstrap',
            default=False,
            type=None,
            help=(
                "Walks the push log, identifying parent and child pushes, "
                "computes/stores metrics data, and populates the "
                "metric_threshold table."
                )
            ),

        make_option(
            '-m',
            '--summary',
            action='store_true',
            dest='summary',
            default=False,
            type=None,
            help=(
                "Computes summary metrics that require data for all "
                "pages in a test suite."
                )
            ),

        make_option("--numdays",
                    action="store",
                    dest="numdays",
                    default=7,
                    help="Number of days worth of pushlogs to return."),

        make_option("--daysago",
                    action="store",
                    dest="daysago",
                    default=None,
                    help=("Number of days ago to start from, "
                          "defaults to now."),
            )
        )


    def handle_project(self, project, options):
        self.stdout.write("Processing project {0}\n".format(project))
        if options.get("bootstrap"):
            push_walker.bootstrap(project, options)
        if options.get("summary"):
            push_walker.summary(project, options)



