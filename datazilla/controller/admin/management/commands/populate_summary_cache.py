"""
This script builds the test run summary data structure for
a 7 and 30 day period interval for every product/branch/version.

These data structures are stored in the summary_cache table.  They
need to persist if the memcache goes down, they take several minutes
to generate.  As the quantity of data grows this will likely take
significantly longer.

"""
from optparse import make_option
import datetime

from datazilla.controller.admin import summary
from django.core.management.base import NoArgsCommand, CommandError

from datazilla.model.sql.models import DataSource


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

        make_option(
            '--cron_batch',
            action='store',
            dest='cron_batch',
            default=False,
            type='int',
            help=(
                "Process all projects with this cron batch number.  " +
                "Causes --project value to be ignored."
                )),
        )


    def handle_noargs(self, **options):
        project = options.get("project")
        cron_batch = options.get("cron_batch")
        if not (project or cron_batch):
            raise CommandError(
                "Must provide either a project or cron_batch value."
                )

        if cron_batch:
            projects = [x.project for x in DataSource.objects.filter(
                contenttype="perftest",
                cron_batch=cron_batch,
                )]
        else:
            projects = [project]

        start = datetime.datetime.now()
        for p in projects:
            self.stdout.write("populate_summary_cache for {0}\n".format(p))

            if options.get("build"):
                summary.build_test_summaries(p)

            if options.get("cache"):
                summary.cache_test_summaries(p)

        finish = datetime.datetime.now()

        duration = finish - start
        self.stdout.write(("populate_summary_cache completed for {0} " +
                           "project(s).  Duration: {1}\n").format(
            len(projects),
            str(duration),
            ))
