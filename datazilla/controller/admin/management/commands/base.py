from optparse import make_option
from abc import abstractmethod

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


    def _get_required_project(self, options):
        """Return the project option if it exists, raise error if not."""
        project = options.get("project")
        if not project:
            raise CommandError(
                "You must supply a project name to create: --project project"
                )
        return project



class ProjectBatchCommandBase(ProjectCommandBase):
    # the valid cron_batch values.  Could also be Null, however.
    BATCH_NAMES = ["small", "medium", "large"]

    option_list = ProjectCommandBase.option_list + (

        make_option(
            '--cron_batch',
            action='append',
            dest='cron_batches',
            choices=BATCH_NAMES,
            help=(
                "Process all projects with this cron batch name.  Can be used "
                "multiple times.  Can not be used with --project command.  "
                "Choices are: {0}".format(", ".join(BATCH_NAMES))
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
        """Handle working on a single project or looping over several."""

        project = options.get("project")
        cron_batches = options.get("cron_batches")

        if options.get("view_batches"):
            # print out each batch that is in use, and the projects
            # that belong to it
            batches = DataSource.get_projects_by_cron_batch()
            for batch, projects in batches.iteritems():
                self.stdout.write("{0}: {1}\n".format(batch, projects))
            return

        if not (project or cron_batches):
            raise CommandError(
                "You must provide either a project or cron_batch value."
            )

        if project and cron_batches:
            raise CommandError(
                "You must provide either project or cron_batch, but not both.")

        if cron_batches:
            projects = DataSource.objects.filter(
                cron_batch__in=cron_batches,
                contenttype="perftest",
                ).values_list("project", flat=True)
        else:
            projects = [project]

        self.stdout.write("Starting for projects: {0}\n".format(", ".join(projects)))

        for p in projects:
            self._handle_one_project(p, options)

        self.stdout.write(
            "Completed for {0} project(s).\n".format(
                len(projects),
                ))


    @abstractmethod
    def _handle_one_project(self, project, options): pass
