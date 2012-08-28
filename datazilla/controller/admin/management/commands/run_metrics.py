from optparse import make_option
from lockfile import FileLock, AlreadyLocked

from datazilla.controller.admin import push_walker
from base import ProjectBatchCommand


class Command(ProjectBatchCommand):

    LOCK_FILE = "run_metrics"

    help = "Run metric methods."

    option_list = ProjectBatchCommand.option_list + (

        make_option("--pushlog_project",
                    action="store",
                    dest="pushlog_project",
                    default="pushlog",
                    help="Push log project name (defaults to pushlog)"),

        make_option(
            '-r',
            '--run_metrics',
            action='store_true',
            dest='run_metrics',
            default=False,
            type=None,
            help=(
                "Walks the push log, identifying parent and child pushes, "
                "computes/stores metrics data, and populates the "
                "metric_threshold table."
                )
            ),

        make_option(
            '-s',
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
                    default=False,
                    help="Number of days worth of pushlogs to return."),

        make_option("--daysago",
                    action="store",
                    dest="daysago",
                    default=False,
                    help=("Number of days ago to start from, "
                          "defaults to now."),
            )
        )


    def handle_project(self, project, options):

        self.stdout.write("Processing project {0}\n".format(project))

        numdays = options.get("numdays")
        run_metrics = options.get("run_metrics")
        summary = options.get("summary")

        if not numdays:
            self.println("You must supply the number of days data.")
            return
        else:
            try:
                numdays = int(numdays)
            except ValueError:
                self.println("numdays must be an integer.")
                return

        if options.get("run_metrics"):
            push_walker.run_metrics(project, options)

        if options.get("summary"):
            push_walker.summary(project, options)

    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))

