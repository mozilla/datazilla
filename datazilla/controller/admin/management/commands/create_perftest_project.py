from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import PerformanceTestModel
from base import ProjectCommandBase, ProjectBatchCommandBase

class Command(ProjectCommandBase):
    """
    Management command to create all databases for a new project.

    This extends ProjectCommandBase rather than ProjectBatchCommandBase
    because the latter handles not just the cron_batch param, but also
    looping.  This mgmt command is not about looping, it's about a single
    project, and about adding that project to a single cron_batch.
    """

    help = "Create all databases for a new project."

    option_list = ProjectCommandBase.option_list + (

        make_option("--perftest_host",
                    action="store",
                    dest="perftest_host",
                    default=None,
                    help="The host name for the perftest database"),

        make_option("--objectstore_host",
                    action="store",
                    dest="objectstore_host",
                    default=None,
                    help="The host name for the objectstore database"),

        make_option("--perftest_type",
                    action="store",
                    dest="perftest_type",
                    default=None,
                    help="The database type (e.g. 'MySQL-InnoDB') "
                    "for the perftest database"),

        make_option("--objectstore_type",
                    action="store",
                    dest="objectstore_type",
                    default=None,
                    help="The database type (e.g. 'MySQL-Aria') "
                    "for the objectstore database"),

        make_option("--cron_batch",
                    action="store",
                    dest="cron_batch",
                    default=None,
                    help=("Which cron_batch this project should belong to. "
                          "Choices are: (0}\n"
                          "Default to none."
                          ).format(str(ProjectBatchCommandBase.BATCH_NAMES))),
        )

    def handle_noargs(self, **options):
        """ Create databases for a new project based on the options value. """

        project = options.get("project")
        cron_batch = options.get("cron_batch")

        if not project:
            raise CommandError(
                "You must supply a project name to create: --project project\n")

        if not cron_batch in ([None] + ProjectBatchCommandBase.BATCH_NAMES):
            raise CommandError(
                "cron_batch must be one of: small, medium or large")

        hosts = dict(
            perftest=options.get("perftest_host"),
            objectstore=options.get("objectstore_host"),
            )

        types = dict(
            perftest=options.get("perftest_type"),
            objectstore=options.get("objectstore_type"),
            )

        dm = PerformanceTestModel.create(
            project,
            hosts=hosts,
            types=types,
            cron_batch=cron_batch,
            )

        dm.disconnect()
