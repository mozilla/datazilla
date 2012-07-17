from optparse import make_option
import datetime

from django.core.management.base import NoArgsCommand, CommandError
from datazilla.model.sql.models import DataSource



class ProjectCommandBase(NoArgsCommand):

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
        )


    def handle_one_project(self, project, options):
        """"""
        raise NotImplementedError


    def handle_noargs(self, **options):
        project = options.get("project")
        self.handle_one_project(project, options)



class ProjectBatchCommandBase(ProjectCommandBase):
    BATCH_NAMES = ["small", "medium", "large"]

    option_list = ProjectCommandBase.option_list + (

        make_option(
            '--cron_batch',
            action='store',
            dest='cron_batch',
            default=False,
            type='string',
            help=(
                "Process all projects with this cron batch name.  " +
                "Can not be used with --project command"
                )),

        make_option(
            '--view_batches',
            action='store_true',
            dest='view_batches',
            default=False,
            type=None,
            help=(
                "Show the cron batches and the projects that belong to them.  "
                "Makes other commands do nothing."
                )),
        )


    def handle_noargs(self, **options):
        project = options.get("project")
        cron_batch = options.get("cron_batch")

        if options.get("view_batches"):
            # print out each batch that is in use, and the projects
            # that belong to it
            batches = DataSource.objects.values_list(
                "cron_batch", flat=True).distinct()
            for batch in batches:
                projnames = DataSource.objects.filter(
                    cron_batch=batch).values_list("project", flat=True)
                self.stdout.write("{0}: {1}\n".format(batch, ", ".join(projnames)))
            return

        if not (project or cron_batch):
            raise CommandError(
                "Must provide either a project or cron_batch value."
            )

        if project and cron_batch:
            raise CommandError(
                "You must provide either project or cron_batch, but not both.")

        if not cron_batch in ([None] + self.BATCH_NAMES):
            raise CommandError(
                "cron_batch must be one of: {0}".format(self.BATCH_NAMES))

        if cron_batch:
            projects = [x.project for x in DataSource.objects.filter(
                contenttype="perftest",
                cron_batch=cron_batch,
                )]
        else:
            projects = [project]

        start = datetime.datetime.now()
        for p in projects:
            self.handle_one_project(p, options)

        finish = datetime.datetime.now()

        duration = finish - start
        self.stdout.write(
            "Completed for {0} project(s).  Duration: {1}\n".format(
                len(projects),
                str(duration),
                ))
