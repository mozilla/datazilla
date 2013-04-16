import signal
import os
import sys
import errno
import time

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import PushLogModel



class Command(BaseCommand):
    """
    Management command to update the pushlog table with the latest pushes.

    example resulting url:
        https://hg.mozilla.org/integration/mozilla-inbound/json-pushes?full=1&startdate=06/04/2012&enddate=06/07/2012


    """
    LOCK_FILE = "update_pushlog"

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

        make_option("--hours",
                    action="store",
                    dest="hours",
                    default=None,
                    help="Number of hours worth of pushlogs to return."),

        # probably mostly for testing purposes, but could be otherwise useful.
        make_option("--branch",
                   action="store",
                   dest="branch",
                   default=None,
                   help="The branch to import pushlogs for (default to all)"),

        # probably mostly for testing purposes, but could be otherwise useful.
        make_option("--project",
                    action="store",
                    dest="project",
                    default=None,
                    help=("The project name for the the pushlog database " +
                          "storage (default to 'pushlog')")),
        )


    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))

    def handle(self, *args, **options):
        """ Store pushlog data in the database. """

        repo_host = options.get("repo_host")
        enddate = options.get("enddate")
        numdays = options.get("numdays")
        hours = options.get("hours")
        branch = options.get("branch")
        verbosity = options.get("verbosity")
        project = options.get("project")

        if not repo_host:
            raise CommandError("You must supply a host name for the repo pushlogs " +
                         "to store: --repo_host hostname")

        if not numdays and not hours:
            raise CommandError("You must supply the number of days or hours of data.")
        else:
            if numdays:
                try:
                    numdays = int(numdays)
                except ValueError:
                    raise CommandError("numdays must be an integer.")

            if hours:

                try:
                    hours = int(hours)
                except ValueError:
                    raise CommandError("hours must be an integer.")

        pidfile = "{0}.pid".format(self.LOCK_FILE)

        if os.path.isfile(pidfile):

            pid = ""
            with open(pidfile) as f:
                pid = f.readline().strip()

            ####
            #If we have a pid file assume the update_pushlog command is
            #hanging on an intermitent urllib timeout from the call to the
            #json-pushes web service method and kill the hanging program.
            ####
            if pid:

                logfile_name = "{0}.log".format(self.LOCK_FILE)
                time_stamp = str( time.time() ).split('.')[0]

                try:

                    os.kill(int(pid), signal.SIGKILL)

                except OSError, err:

                    log_file = open(logfile_name, 'a+')

                    msg = ""
                    if err.errno == errno.ESRCH:
                        msg = "pid:{0} time:{1}, Not running\n".format(
                            pid, time_stamp)
                    elif err.errno == errno.EPERM:
                        msg = "pid:{0} time:{1}, No permission to signal process\n".format(
                            pid, time_stamp)
                    else:
                        msg = "pid:{0} time:{1}, Generated unknown error {2}\n".format(
                            pid, str(err), time_stampe)

                    log_file.write(msg)
                    log_file.close()

                    #make sure we get rid of any pid file on error
                    os.unlink(pidfile)

                else:

                    #log the kill
                    log_file = open(logfile_name, 'a+')
                    log_file.write("pid:{0} time:{1}, Killed\n".format(
                        pid, time_stamp))
                    log_file.close()

                    #remove any existing pidfile
                    os.unlink(pidfile)

        #Write pid file
        pid = str(os.getpid())
        file(pidfile, 'w').write(pid)

        plm = PushLogModel(project=project, out=self.stdout, verbosity=verbosity)

        # store the pushlogs for the branch specified, or all branches
        summary = plm.store_pushlogs(repo_host, numdays, hours, enddate, branch)
        self.println(("Branches: {0}\nPushlogs stored: {1}, skipped: {2}\n" +
                      "Changesets stored: {3}, skipped: {4}").format(
                        summary["branches"],
                        summary["pushlogs_stored"],
                        summary["pushlogs_skipped"],
                        summary["changesets_stored"],
                        summary["changesets_skipped"],
            ))

        plm.disconnect()

        os.unlink(pidfile)


