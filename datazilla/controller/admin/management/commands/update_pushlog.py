from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import PushLogModel
from django.conf import settings



class Command(BaseCommand):
    """
    Management command to update the pushlog table with the latest pushes.

    example resulting url:
        https://hg.mozilla.org/integration/mozilla-inbound/json-pushes?full=1&startdate=06/04/2012&enddate=06/07/2012


    """

    help = "Update the repo pushlog table."

    option_list = BaseCommand.option_list + (

        make_option("--repo_host",
                    action="store",
                    dest="repo_host",
                    default=None,
                    help="The host name for the repo (e.g. hg.mozilla.org)"),

        make_option("--enddate",
                    action="store",
                    dest="enddate",
                    default=None,
                    help="(optional) The ending date range for pushlogs in " +
                         "the format: MM/DD/YYYY.  Default to today."),

        make_option("--numdays",
                    action="store",
                    dest="numdays",
                    default=None,
                    help="Number of days worth of pushlogs to return."),

        # probably mostly for testing purposes, but could be otherwise useful.
        make_option("--branch",
                   action="store",
                   dest="branch",
                   default=None,
                   help="The branch to import pushlogs for (default to all)"),
        )


    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))


    def handle(self, *args, **options):
        """ Store pushlog data in the database. """

        repo_host = options.get("repo_host")
        enddate = options.get("enddate")
        numdays = options.get("numdays")
        branch = options.get("branch")
        verbosity = options.get("verbosity")

        if not repo_host:
            self.println("You must supply a host name for the repo pushlogs " +
                         "to store: --repo_host hostname")
            return

        if not numdays:
            self.println("You must supply the number of days data.")
            return
        else:
            try:
                numdays = int(numdays)
            except ValueError:
                self.println("numdays must be an integer.")
                return

        plm = PushLogModel(out=self.stdout, verbosity=verbosity)

        # store the pushlogs for the branch specified, or all branches
        summary = plm.store_pushlogs(repo_host, numdays, enddate, branch)
        self.println(("Branches: {0}\nPushlogs stored: {1}, skipped: {2}\n" +
                      "Changesets stored: {3}, skipped: {4}").format(
                summary["branches"],
                summary["pushlogs_stored"],
                summary["pushlogs_skipped"],
                summary["changesets_stored"],
                summary["changesets_skipped"],
                ))
        plm.hg_ds.disconnect()

