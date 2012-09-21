import json
from optparse import make_option

from django.core.management.base import CommandError

from datazilla.model import PerformanceTestModel, PushLogModel, utils
from datazilla.controller.admin.refdata import pushlog_refdata
from base import ProjectCommand



class Command(ProjectCommand):
    """
    Find pushlog entries without matching test results.

    Compare perftest test_run.revision field with pushlog revision field
    for a project.  Anything in one and not in the other for the date range
    will be reported.

    """
    help = (
        "Check each pushlog entry for a project and report any changeset"
        "that doesn't have test data for it."
        )

    option_list = ProjectCommand.option_list + (


        make_option("--days_ago",
                action="store",
                dest="days_ago",
                default=None,
                help="The number of days prior to today to use as the starting"
                    "date range.",
                ),

        make_option("--numdays",
                action="store",
                dest="numdays",
                default=None,
                help="Number of days since days_ago to use as the end date for"
                    "the date range.",
                ),

        make_option("--branches",
                    action="store",
                    dest="branches",
                    default=None,
                    help="Comma separated list of branches to check.  "
                        "Default to all branches.",
                    ),

        )


    def handle_project(self, project, **options):
        """Report pushlogs not referenced with tests in the project."""

        self.stdout.write("Processing project {0}\n".format(project))

        days_ago = options.get("days_ago")
        if not days_ago:
            raise CommandError(
                "You must supply days_ago."
            )
        numdays = options.get("numdays")
        branches = options.get("branches")

        range = utils.get_day_range(days_ago, numdays)
        if branches:
            branches = branches.split(",")
        else:
            branches = pushlog_refdata.get_all_branches()


        stats = pushlog_refdata.get_not_referenced(
            project,
            range["start"],
            range["stop"],
            branches,
            )
        print json.dumps(stats, indent=4)
        return
