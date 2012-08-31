from optparse import make_option

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

        make_option("--numdays",
                    action="store",
                    dest="numdays",
                    default=None,
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
        daysago = options.get("daysago")
        pushlog_project = options.get("pushlog_project")

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

        push_walker.run_metrics(
            project, pushlog_project, numdays, daysago
            )

        push_walker.summary(project, pushlog_project, numdays, daysago)


    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))

