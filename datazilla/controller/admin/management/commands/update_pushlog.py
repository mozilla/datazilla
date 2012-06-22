from MySQLdb import IntegrityError
from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import PushLogModel
import urllib
import json
import datetime
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
        )


    def println(self, val):
        self.stdout.write("{0}\n".format(str(val)))


    def handle(self, *args, **options):
        """ Store pushlog data in the database. """

        repo_host = options.get("repo_host")
        enddate = options.get("enddate")
        numdays = int(options.get("numdays"))

        if not repo_host:
            self.println("You must supply a host name for the repo pushlogs " +
                         "to store: --repo_host hostname")
            return

        if not numdays:
            self.println("You must supply the number of days data.")
            return

        # parameters sent to the requests for pushlog data
        params = self.get_params(enddate, numdays)

        plm = PushLogModel()

        #####
        # Loop through all branches for all pushlogs

        # fetch the list of known branches.

        for branch in plm.get_all_branches():
            self.println("Branch: pushlogs for {0}".format(branch["name"]))

            uri = "{0}/json-pushes".format(branch["uri"])

            url = "https://{0}/{1}?{2}".format(
                repo_host,
                uri,
                urllib.urlencode(params),
                )

            if settings.DEBUG:
                self.println("URL: {0}".format(url))

            # fetch the JSON content from the constructed URL.
            res = urllib.urlopen(url)

            json_data = res.read()
            pushlog_list = json.loads(json_data)

            self.insert_pushlog(plm.hg_ds, branch["id"], pushlog_list)

        plm.disconnect()


    def get_params(self, enddate, numdays):
        """figure out the params to send to the pushlog queries."""

        if enddate:
            #create a proper datetime.date for calculation of startdate
            m, d, y = enddate.split("/")
            _enddate = datetime.date(month=int(m), day=int(d), year=int(y))
        else:
            _enddate = datetime.date.today()

        # calculate the startdate and enddate

        _startdate = _enddate - datetime.timedelta(days=numdays)

        params = {
            "full": 1,
            "startdate": _startdate.strftime("%m/%d/%y"),
            }
        # enddate is optional.  the endpoint will just presume today,
        # if not given.
        if enddate:
            params.update({"enddate": enddate})

        return params


    def insert_pushlog(self, ds, branch_id, pushlog_list):
        """Loop through all the pushlogs and insert them."""

        for pushlog_json_id, pushlog in pushlog_list.items():
            # make sure the push_log_id isn't confused with a previous iteration
            self.println("    Pushlog {0}".format(pushlog_json_id))

            placeholders = [
                pushlog_json_id,
                pushlog["date"],
                pushlog["user"],
                branch_id,
                ]
            try:
                pushlog_id = self._insert_data_and_get_id(
                    ds,
                    "set_push_log",
                    placeholders=placeholders,
                    )

                # process the nodes of the pushlog
                self.insert_changesets(ds, pushlog_id, pushlog["changesets"])

            except IntegrityError:
                self.println("<><><>Skip dup- pushlog: {0}".format(
                    pushlog_json_id,
                ))


    def insert_changesets(self, ds, pushlog_id, changeset_list):
        """Loop through all the changesets in a pushlog, and insert them."""

        for cs in changeset_list:
            self.println("        Changeset {0}".format(cs["node"]))
            placeholders = [
                cs["node"],
                cs["author"],
                cs["branch"],
                cs["desc"],
                pushlog_id,
                ]

            try:
                changeset_id = self._insert_data_and_get_id(
                    ds,
                    "set_node",
                    placeholders=placeholders,
                    )

                # process the files of nodes
                self.insert_files(ds, changeset_id, cs["files"])

            except IntegrityError:
                self.println("<><><>Skip changeset dup- pushlog: {0}, node: {1}".format(
                    pushlog_id,
                    cs["node"],
                    ))


    def insert_files(self, ds, changeset_id, file_list):
        """Insert all the files in the changeset"""

        for file in file_list:
            placeholders = [
                changeset_id,
                file,
                ]
            try:
                self._insert_data(
                    ds,
                    "set_file",
                    placeholders=placeholders,
                    )
            except IntegrityError:
                self.println("<><><>Skip dup- node: {1}, file: {2}".format(
                    pushlog_json_id,
                    node_id,
                    file,
                    ))


    def _insert_data(self, ds, statement, placeholders, executemany=False):

        return ds.dhub.execute(
            proc='hgmozilla.inserts.' + statement,
            debug_show=settings.DEBUG,
            placeholders=placeholders,
            executemany=executemany,
            return_type='iter',
            )


    def _insert_data_and_get_id(self, ds, statement, placeholders):

        self._insert_data(ds, statement, placeholders)

        id_iter = ds.dhub.execute(
            proc='hgmozilla.selects.get_last_insert_id',
            debug_show=settings.DEBUG,
            return_type='iter',
            )

        return id_iter.get_column_data('id')


