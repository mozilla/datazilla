import json
from optparse import make_option

from django.core.management.base import CommandError

from datazilla.model import utils
from datazilla.controller.admin.stats import objectstore_stats
from base import ProjectCommand

class Command(ProjectCommand):
    """Display a report of which objectstore entries had an error."""

    help = (
        "Generate a report of all the JSON data that had an error "
        "and could, therefore, not be processed."
        )

    option_list = ProjectCommand.option_list + (

        make_option(
            '-l',
            '--list',
            action='store_true',
            dest='show_list',
            default=False,
            type=None,
            help="Show a list of errors."
        ),

        make_option(
            '--simple_count',
            action='store_true',
            dest='show_simple_count',
            default=False,
            type=None,
            help="Show a simple count of error types."
        ),

        make_option(
            '--detail_count',
            action='store_true',
            dest='show_detail_count',
            default=False,
            type=None,
            help="Show a detailed count of error types broken down by name, "
                "branch and version.  This requires inspecting the JSON blob "
                "and a chunking query, so it can take quite a while based on"
                "the date range."
        ),

        make_option(
            "--days_ago",
            action="store",
            dest="days_ago",
            default=None,
            help="The number of days prior to today to use as the starting"
                "date range.",
            ),

        make_option(
            "--numdays",
            action="store",
            dest="numdays",
            default=None,
            help="Number of days since days_ago to use as the end date for"
                "the date range.",
            ),

        )


    def handle_project(self, project, **options):
        """Count errors of the project grouped by name, branch and version."""

        self.stdout.write("Processing project {0}\n".format(project))

        days_ago = options.get("days_ago")
        if not days_ago:
            raise CommandError(
                "You must supply days_ago."
            )
        numdays = options.get("numdays")

        range = utils.get_day_range(days_ago, numdays)
        if options.get("show_list"):
            err_list = objectstore_stats.get_error_list(
                project,
                range["start"],
                range["stop"],
                )
            self.stdout.write(json.dumps(err_list, indent=4))

        if options.get("show_simple_count"):
            err_count = objectstore_stats.get_error_count(
                project,
                range["start"],
                range["stop"],
                )
            self.stdout.write(json.dumps(err_count, indent=4))


        if options.get("show_detail_count"):
            err_count = objectstore_stats.get_error_detail_count(
                project,
                range["start"],
                range["stop"],
                )
            ptm.disconnect()
            self.stdout.write(json.dumps(err_count, indent=4))
