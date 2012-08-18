"""
This script builds the test run summary data structure for
a 7 and 30 day period interval for every product/branch/version.

These data structures are stored in the summary_cache table.  They
need to persist if the memcache goes down, they take several minutes
to generate.  As the quantity of data grows this will likely take
significantly longer.

"""
from optparse import make_option
from lockfile import FileLock, AlreadyLocked

from datazilla.controller.admin import push_walker
from base import ProjectBatchCommand


class Command(ProjectBatchCommand):

    LOCK_FILE = "run_metrics"

    help = "Run metric methods."

    option_list = ProjectBatchCommand.option_list + (

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

            #Get a lock name unique for the option
            lock = FileLock("{0}_{1}".format(self.LOCK_FILE,"_run_metrics"))
            try:
                lock.acquire(timeout=0)
                try:
                    push_walker.run_metrics(project, options)
                finally:
                    lock.release()

            except AlreadyLocked:
                self.println(
                    ("This command is already being run elsewhere.  Please "
                     "try again later.")
                     )


        if options.get("summary"):
            #Get a lock name unique for the option
            lock = FileLock("{0}_{1}".format(self.LOCK_FILE,"_summary"))
            try:
                lock.acquire(timeout=0)
                try:
                    push_walker.summary(project, options)
                finally:
                    lock.release()

            except AlreadyLocked:
                self.println(
                    ("This command is already being run elsewhere.  Please "
                     "try again later.")
                     )

    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))

