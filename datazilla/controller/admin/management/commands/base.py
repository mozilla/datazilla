from optparse import make_option
from abc import abstractmethod
from lockfile import FileLock, AlreadyLocked

from django.core.management.base import NoArgsCommand, CommandError

from datazilla.model.sql.models import CRON_BATCH_NAMES
from datazilla.model.base import PerformanceTestModel


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
                "You must supply a project name: --project project"
                )
        return project



class ProjectBatchCommandBase(ProjectCommandBase):
    """
    Base class for executing a management command against a batch
    of projects.

    Concurrency locking:
    To set a custom lock-file for a command, assign a value to
    self.lock_file.  Otherwise, it will use DEFAULT_LOCK_FILE.
    """

    LOCK_FILE = "cron_batch"

    option_list = ProjectCommandBase.option_list + (

        make_option(
            '--cron_batch',
            action='append',
            dest='cron_batches',
            choices=CRON_BATCH_NAMES,
            help=(
                "Process all projects with this cron batch name.  Can be used "
                "multiple times.  Can not be used with --project command.  "
                "This value indicates the size of the project and may determine "
                "how much time between intervals should be set.  Larger "
                "projects will likely have a longer time interval between " \
                "execution as cron jobs."
                "Choices are: {0}".format(", ".join(CRON_BATCH_NAMES))
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
            if project or cron_batches:
                raise CommandError(
                    "view_batches can not be used with project or cron_batch"
                )
            # print out each batch that is in use, and the projects
            # that belong to it
            batches = PerformanceTestModel.get_projects_by_cron_batch()
            for key in sorted(batches.keys()):
                self.stdout.write("{0}: {1}\n".format(key, batches[key]))
            return

        if not (project or cron_batches):
            raise CommandError(
                "You must provide either a project or cron_batch value."
            )

        if project and cron_batches:
            raise CommandError(
                "You must provide either project or cron_batch, but not both.")

        if cron_batches:
            projects = PerformanceTestModel.get_cron_batch_projects(cron_batches)
        else:
            projects = [project]

        lock = FileLock(self.LOCK_FILE)
        try:
            lock.acquire(timeout=0)
            try:
                self.stdout.write(
                    "Starting for projects: {0}\n".format(", ".join(projects)))

                for p in projects:
                    self.handle_one_project(p, options)

                self.stdout.write(
                    "Completed for {0} project(s).\n".format(len(projects)))
            finally:
                lock.release()

        except AlreadyLocked:
            self.stdout.write("This command is already being run elsewhere.  "
            "Please try again later.\n")


    @abstractmethod
    def handle_one_project(self, project, options): pass
