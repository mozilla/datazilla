import os

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from datazilla.model import DatazillaModel
from django.conf import settings

import oauth2 as oauth
import time
import urllib
import httplib

class Command(BaseCommand):

    help = (
            "HTTP POST a JSON object to api/load_test"
            )

    option_list = BaseCommand.option_list + (
        make_option('--project',
                    action='store',
                    dest='project',
                    default=False,
                    help='Source project to pull data from: talos, ' +
                         'b2g, stoneridge, test etc...'),

        make_option('--host',
                    action='store',
                    dest='host',
                    default=False,
                    help='The host to post data to.'),

        make_option('--file',
                    action='store',
                    dest='file',
                    default=False,
                    help='Absolute path to file containing JSON.'),

        make_option('--key',
                    action='store',
                    dest='consumer_key',
                    default=settings.OAUTH_CONSUMER_KEY,
                    help='Provide the OAuth consumer key for this ' +
                         'project. This defaults to ' +
                         'settings.OAUTH_CONSUMER_KEY.'),

        make_option('--secret',
                    action='store',
                    dest='consumer_secret',
                    default=settings.OAUTH_CONSUMER_SECRET,
                    help='Provide the OAuth consumer secret for this ' +
                         'project. This defaults to ' +
                         'settings.OAUTH_CONSUMER_SECRET.'),

        make_option('--debug',
                    action='store_true',
                    dest='debug',
                    default=None,
                    help='Write out HTTP header and post data to stdout ' +
                         'without sending.'))

    def handle(self, *args, **options):

        project             = options.get('project')
        host                = options.get('host')
        file                = options.get('file')
        consumer_key        = options.get('consumer_key')
        consumer_secret     = options.get('consumer_secret')
        debug               = options.get('debug')

        if not project:
            self.stdout.write("You must supply a project name" +
                              " to POST data to: --project project\n")
            return

        if not host:
            self.stdout.write("You must supply a host name" +
                              " to POST data to: --host host\n")
            return

        if not os.path.isfile(file):
            self.stdout.write("You must supply a JSON file" +
                              " to POST: --file JSON file\n")
            return

        if not consumer_key:
            self.stdout.write("You must supply the projects consumer key" +
                              " to POST: --key key or" +
                              " settings.OAUTH_CONSUMER_KEY\n")
            return

        if not consumer_secret:
            self.stdout.write("You must supply the projects consumer" +
                              " secret to POST: --key key or" +
                              " settings.OAUTH_CONSUMER_KEY\n")
            return

        ##Open the json file##
        f = open( file )
        json_file = f.read()
        f.close()

        uri = 'http://%s/%s/api/load_test' % (host, project)

        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'user': project,
            'data': urllib.quote(json_file)
        }

        #There is no requirement for the token in two-legged
        #OAuth but we still need the token object.
        token = oauth.Token(key="", secret="")
        consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

        params['oauth_token'] = token.key
        params['oauth_consumer_key'] = consumer.key
        headers = {"Content-type":"application/x-www-form-urlencoded",
                   "Accept":"text/plain"}

        req = oauth.Request(method="POST", url=uri, parameters=params)

        #Set the signature
        signature_method = oauth.SignatureMethod_HMAC_SHA1()

        #Sign the request
        req.sign_request(signature_method, consumer, token)

        #Build the header
        header = req.to_header()
        header['Content-type'] = 'application/x-www-form-urlencoded'
        header['Accept'] = 'text/plain'

        if debug:

            self.stdout.write(str(headers) + "\n")
            self.stdout.write(req.to_postdata() + "\n")

        else:

            conn = httplib.HTTPConnection(host)

            conn.request("POST", uri, req.to_postdata(), headers)
            response = conn.getresponse()

            self.stdout.write("status:%s\nreason:%s\nresponse:%s\n" %
                (response.status, response.reason, response.read()))

