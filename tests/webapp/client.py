"""
Webapp integration test client.

"""
import json
import time
import urllib

from django.core.handlers.wsgi import WSGIHandler
from django_webtest.middleware import DjangoWsgiFix
from webtest import TestApp



class TestClient(TestApp):
    """
    A WebTest-based test client for webapp integration tests.

    """
    def __init__(self, *args, **kwargs):
        super(TestClient, self).__init__(
            self.get_wsgi_application(), *args, **kwargs)


    def get_wsgi_application(self):
        return DjangoWsgiFix(WSGIHandler())


    def oauth_post(self, ptm, path, data):
        """Post data to url using OAuth creds from given PerfTestModel."""
        import oauth2 as oauth

        uri = "http://localhost:80%s" % path
        user = ptm.project
        ds = ptm.sources["objectstore"].datasource
        oauth_key = ds.oauth_consumer_key
        oauth_secret = ds.oauth_consumer_secret

        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'user': user,
            'data': urllib.quote(json.dumps(data)),
        }

        #There is no requirement for the token in two-legged
        #OAuth but we still need the token object.
        token = oauth.Token(key="", secret="")
        consumer = oauth.Consumer(key=oauth_key, secret=oauth_secret)

        params['oauth_token'] = token.key
        params['oauth_consumer_key'] = consumer.key

        req = oauth.Request(method="POST", url=uri, parameters=params)

        #Set the signature
        signature_method = oauth.SignatureMethod_HMAC_SHA1()

        #Sign the request
        req.sign_request(signature_method, consumer, token)

        #Build the header
        header = {'Content-type': 'application/x-www-form-urlencoded'}

        return self.post(path, req, headers=header)
