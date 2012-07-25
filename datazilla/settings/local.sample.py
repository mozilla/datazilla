"""
Sample Datazilla local-settings.

Copy this file to ``local.py`, then uncomment and modify the below settings as
needed for your configuration.

"""
import os

# Database connection parameters
DATAZILLA_DATABASE_NAME     = os.environ.get("DATAZILLA_DATABASE_NAME", "")
DATAZILLA_DATABASE_USER     = os.environ.get("DATAZILLA_DATABASE_USER", "")
DATAZILLA_DATABASE_PASSWORD = os.environ.get("DATAZILLA_DATABASE_PASSWORD", "")
DATAZILLA_DATABASE_HOST     = os.environ.get("DATAZILLA_DATABASE_HOST", "")
DATAZILLA_DATABASE_PORT     = os.environ.get("DATAZILLA_DATABASE_PORT", "")

DATAZILLA_MEMCACHED         = os.environ.get("DATAZILLA_MEMCACHED", "")

# base URL
DATAZILLA_URL               = os.environ.get("DATAZILLA_URL", "/")

# This should always be False in production
DEBUG = os.environ.get("DATAZILLA_DEBUG") is not None

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ["DATAZILLA_DJANGO_SECRET_KEY"]

# Make this unique so that when you execute the unit tests, you don't conflict
# with other people running the unit tests.
UNIT_TEST_PREFIX="user_"