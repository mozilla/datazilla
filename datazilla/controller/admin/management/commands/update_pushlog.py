from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model.sql.models import SQLDataSource
import urllib
import json
import datetime



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

        make_option("--uri",
                    action="store",
                    dest="uri",
                    default="integration/mozilla-inbound/json-pushes",
                    help="(optional) The URI for fetching the pushlogs from " +
                    "the given repo_host."),

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

    def handle(self, *args, **options):
        """ Store pushlog data in the database. """

        repo_host = options.get("repo_host")
        uri = options.get("uri")
        enddate = options.get("enddate")
        numdays = int(options.get("numdays"))

        if not repo_host:
            self.stdout.write("You must supply a host name for the repo pushlogs " +
                              "to store: --repo_host hostname\n")
            return

        if not numdays:
            self.stdout.write("You must supply the number of days data.\n")
            return

        if enddate:
            #create a proper datetime.date for calculation of startdate
            m, d, y = enddate.split("/")
            _enddate = datetime.date(month=int(m), day=int(d), year=int(y))
        else:
            _enddate = datetime.date.today()

        # calcualte the startdate

        _startdate = _enddate - datetime.timedelta(days=numdays)

        params = {
            "full": 1,
            "startdate": _startdate.strftime("%m/%d/%y"),
        }
        # enddate is optional.  the endpoint will just presume today,
        # if not given.
        if enddate:
            params.update({"enddate": enddate})

        url = "https://{0}/{1}?{2}".format(
            repo_host,
            uri,
            urllib.urlencode(params)
        )

        # fetch the JSON content from the constructed URL.
        res = urllib.urlopen(url)

        json_data = res.read()
        data = json.loads(json_data)

        ds = SQLDataSource(repo_host, "pushlog")

        # one pushlog
        for k, v in data.items():
            placeholders = [
                k,
                v["date"],
                v["user"]
            ]
            iter = self._insert_data(
                ds,
                "set_push_log",
                placeholders=placeholders,
                )
            # TODO How do I determine if I inserted a new row or not?
            # If not, I don't want to do the child items

            for i in iter:
                print i

            # now process the nodes

        ds.disconnect()

#        print json.dumps(data, indent=4)


    def _insert_data(self, ds, statement, placeholders, executemany=False):

        return ds.dhub.execute(
            proc='pushlog.inserts.' + statement,
            debug_show=False,
            placeholders=placeholders,
            executemany=executemany,
            return_type='iter',
            )


    def _insert_data_and_get_id(self, ds, statement, placeholders):

        self._insert_data(ds, statement, placeholders)

        id_iter = ds.dhub.execute(
            proc='pushlog.selects.get_last_insert_id',
            debug_show=self.DEBUG,
            return_type='iter',
            )

        return id_iter.get_column_data('id')


