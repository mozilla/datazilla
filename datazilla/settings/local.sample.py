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

DATAZILLA_RO_DATABASE_USER     = os.environ.get("DATAZILLA_RO_DATABASE_USER", "")
DATAZILLA_RO_DATABASE_PASSWORD = os.environ.get("DATAZILLA_RO_DATABASE_PASSWORD", "")

DATAZILLA_MEMCACHED         = os.environ.get("DATAZILLA_MEMCACHED", "")

# base URL
DATAZILLA_URL               = os.environ.get("DATAZILLA_URL", "/")

#pipe delimited list of allowed project names, defaults to \w+ if not set
ALLOWED_PROJECTS            = os.environ.get("ALLOWED_PROJECTS", "")

# This should always be False in production
DEBUG = os.environ.get("DATAZILLA_DEBUG") is not None

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get("DATAZILLA_DJANGO_SECRET_KEY", "")

# Make this unique so that if you execute the tests against a shared database,
# you don't conflict with other people running the tests simultaneously.
TEST_DB_PREFIX="test_"

DATAZILLA_PROJECT_UI = { 'talos':'summary' }
