"""
This script builds the test run summary data structure for
a 7 and 30 day period interval for every product/branch/version.

These data structures are stored in the summary_cache table.  They
need to persist if the memcache goes down, they take several minutes
to generate.  As the quantity of data grows this will likely take
significantly longer.

"""
from optparse import make_option


from datazilla.controller.admin import summary
from django.core.management.base import NoArgsCommand, CommandError



class Command(NoArgsCommand):
    help = "Populate the summary cache for a project."

    option_list = NoArgsCommand.option_list + (
        make_option(
            '-p',
            '--project',
            action='store',
            dest='project',
            default=False,
            type='string',
            help="Set the project to run on: talos, b2g, schema, test etc....",
            ),

        make_option(
            '-b',
            '--build',
            action='store_true',
            dest='build',
            default=False,
            type=None,
            help="Build the test run summaries and store them in the database."
            ),

        make_option(
            '-c',
            '--cache',
            action='store_true',
            dest='cache',
            default=False,
            type=None,
            help="Update the test run summaries in memcached",
            ),
        )


    def handle_noargs(self, **options):
        project = options.get("project")
        if not project:
            raise CommandError("No project argument provided.")

        if options.get("build"):
            summary.build_test_summaries(project)

        if options.get("cache"):
            summary.cache_test_summaries(project)
