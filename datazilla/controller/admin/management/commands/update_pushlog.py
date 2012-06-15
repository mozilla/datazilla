from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import DatazillaModel
import urllib
import json

class Command(BaseCommand):
    """
    Management command to update the pushlog table with the latest pushes.

https://hg.mozilla.org/integration/mozilla-inbound/json-pushes?full=1&startdate=06/04/2012&enddate=06/07/2012
    This will need:
      host
      uri
      startdate
      enddate

    must ensure we are not persisting duplicates, so must do a get on each
    pushlog_id

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
                    help="The URI for fetching the pushlogs from the given repo_host."),

        make_option("--startdate",
                    action="store",
                    dest="startdate",
                    default=None,
                    help="The beginning date range for pushlogs"),

        make_option("--enddate",
                    action="store",
                    dest="enddate",
                    default=None,
                    help="The ending date range for pushlogs"),

        make_option("--maxdays",
                    action="store",
                    dest="maxdays",
                    default=10,
                    help="The ending date range for pushlogs"),
        )

    def handle(self, *args, **options):
        """ Store pushlog data in the database. """

        repo_host = options.get("repo_host")
        uri = options.get("uri")
        startdate = options.get("startdate")
        enddate = options.get("enddate")


        if not repo_host:
            self.stdout.write("You must supply a host name for the repo pushlogs " +
                              "to store: --repo_host hostname\n")
            return

        params = {
            "full": 1,
            "startdate": startdate,
            "enddate": enddate,
        }

        url = "https://{0}/{1}?{2}".format(
            repo_host,
            uri,
            urllib.urlencode(params)
        )
        # fetch the JSON content from the constructed URL.
        res = urllib.urlopen(url)

        json_data = res.read()
        data = json.loads(json_data)
        print json.dumps(data, indent=4)

#        dm = DatazillaModel.create(project, hosts=hosts, types=types)
#
#        dm.disconnect()
