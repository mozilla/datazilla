"""
Webapp integration test client.

"""
from django.core.handlers.wsgi import WSGIHandler
from django_webtest.middleware import DjangoWsgiFix
from webtest import TestApp

from .oauth import oauth_signed



class TestClient(TestApp):
    """
    A WebTest-based test client for webapp integration tests.

    """
    def __init__(self, *args, **kwargs):
        super(TestClient, self).__init__(
            self.get_wsgi_application(), *args, **kwargs)


    def get_wsgi_application(self):
        return DjangoWsgiFix(WSGIHandler())


    def oauth_post(self, ptm, data=None, **kwargs):
        """Post data to url using OAuth creds from given PerfTestModel."""
        path = "/%s/api/load_test" % ptm.project
        signed_data = oauth_signed(ptm, path, data)
        return self.post(path, signed_data, **kwargs)
