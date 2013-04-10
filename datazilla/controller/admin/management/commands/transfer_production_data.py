import urllib
import socket
import sys
import json
import os

from optparse import make_option
from django.core.management.base import BaseCommand
from datazilla.model import PushLogModel
from datazilla.model import PerformanceTestModel

class Command(BaseCommand):
    """Transfer json objects from production database to development objectstore database."""

    help = "Transfer json objects from production database to development objectstore database."

    option_list = BaseCommand.option_list + (
        make_option('--host',
                    action='store',
                    dest='host',
                    default='datazilla.mozilla.org',
                    help='Production host to transfer data from'),

        make_option("--dev_project",
                    action="store",
                    dest="dev_project",
                    default=None,
                    help=("The project name in development to transfer data to.")),

        make_option("--prod_project",
                    action="store",
                    dest="prod_project",
                    default='talos',
                    help=("The project name in production to transfer data from.")),

        make_option("--days_ago",
                    action="store",
                    dest="days_ago",
                    default="7",
                    help=("Number of days to retrieve data for")),

        make_option("--branch",
                    action="store",
                    dest="branch",
                    default="Mozilla-Inbound",
                    help=("The branch name to transfer data from.")),

        make_option("--logfile",
                    action="store",
                    dest="logfile",
                    default="{0}/transfer_production_data.log".format(os.getcwd()),
                    help=("Log of revisions run.")),
        )

    def handle(self, *args, **options):
        """ Transfer data to a development project based on the args value. """

        host = options.get("host")
        dev_project = options.get("dev_project")
        prod_project = options.get("prod_project")
        branch = options.get("branch")
        days_ago = options.get("days_ago")
        logfile = options.get("logfile")

        if not host:
            self.println("You must supply a host name to retrieve data from " +
                     "--host hostname")
            return

        if not dev_project:
            self.println("You must supply a dev_project name to load data in.")
            return

        if not branch:
            self.println("You must supply a branch name to retrieve data for.")
            return

        #Set timeout so we don't hang
        timeout = 120
        socket.setdefaulttimeout(timeout)

        revisions_uri = 'refdata/pushlog/list'
        params = 'days_ago={0}&branches={1}'.format(days_ago, branch)
        url = "https://{0}/{1}?{2}".format(host, revisions_uri, params)

        json_data = ""

        #Retrieve revisions to iterate over
        try:
            response = urllib.urlopen(url)
            json_data = response.read()
        except socket.timeout:
            self.stdout.write( "URL: {0}\nTimedout {1} seconds\n".format(
                url, timeout
                ) )
            sys.exit(0)

        data = json.loads(json_data)
        all_keys = data.keys()
        all_keys.sort()

        ##Keep track of revision already loaded##
        file_obj = open(logfile, 'w+')
        revisions_seen = set()
        for line in file_obj.readlines():
            revisions_seen.add(line.strip())

        revisions = []

        for key in all_keys:
            for revision in data[key]['revisions']:
                if revision not in revisions_seen:
                    revisions.append(revision)

        dm = PerformanceTestModel(dev_project)

        for revision in revisions:

            rawdata_uri = '{0}/testdata/raw/{1}/{2}/'.format(
                prod_project, branch, revision
                )
            rawdata_url = "https://{0}/{1}".format(host, rawdata_uri)

            raw_json_data = ""

            try:
                rawdata_response = urllib.urlopen(rawdata_url)
                raw_json_data = rawdata_response.read()
            except socket.timeout:
                self.stdout.write( "URL: {0}\nTimedout {1} seconds\n".format(
                    rawdata_url, timeout) )
                sys.exit(0)

            test_object_data = json.loads(raw_json_data)

            for test_object in test_object_data:
                id = dm.store_test_data( json.dumps(test_object), "" )
                self.stdout.write( "Revision:{0} Id:{1}\n".format(revision, str(id)))

            #Record the revision as loaded
            file_obj.write(revision + "\n")

        file_obj.close()
        dm.disconnect()



