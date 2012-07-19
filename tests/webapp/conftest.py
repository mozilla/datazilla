"""
Test config for webapp tests.

"""


def pytest_funcarg__client(request):
    """
    Give a test access to a WebTest client.

    """
    from django.conf import settings

    from tests.webapp.client import TestClient

    # Exceptions in tests are easier to debug if they are propagated rather
    # than caught and replaced by Django with the technical 500 response.
    _old_debug_propagate = settings.DEBUG_PROPAGATE_EXCEPTIONS
    def unpatch_settings():
        settings.DEBUG_PROPAGATE_EXCEPTIONS = _old_debug_propagate
    request.addfinalizer(unpatch_settings)

    return TestClient()
