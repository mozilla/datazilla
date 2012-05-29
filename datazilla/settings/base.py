# Django settings for webapp project.
import os, posixpath

USE_APP_ENGINE = "APPENGINE_RUNTIME" in os.environ or os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or os.getenv('SETTINGS_MODE') == 'prod'

# These settings can all be optionally set via env vars, or in local.py:

# Set Database connectivity via environment
DATAZILLA_DATABASE_NAME     = os.environ.get("DATAZILLA_DATABASE_NAME", "")
DATAZILLA_DATABASE_USER     = os.environ.get("DATAZILLA_DATABASE_USER", "")
DATAZILLA_DATABASE_PASSWORD = os.environ.get("DATAZILLA_DATABASE_PASSWORD", "")
DATAZILLA_DATABASE_HOST     = os.environ.get("DATAZILLA_DATABASE_HOST", "")
DATAZILLA_DATABASE_PORT     = os.environ.get("DATAZILLA_DATABASE_PORT", "")

DATAZILLA_MEMCACHED         = os.environ.get("DATAZILLA_MEMCACHED", "")

# Set base URL via the environment
DATAZILLA_URL               = os.environ.get("DATAZILLA_URL", "/")

DEBUG = os.environ.get("DATAZILLA_DEBUG") is not None

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get("DATAZILLA_DJANGO_SECRET_KEY", "")


ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
path = lambda *a: os.path.join(ROOT, *a)

ADMINS = [
   ("jeads", "jeads@mozilla.com"),
   ("Carl Meyer", "cmeyer@mozilla.com"),
]

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "America/Los_Angeles"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
#STATIC_ROOT = path("datazilla/webapp/collected-assets")

# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path("datazilla/webapp/static"),
]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
#    "django.contrib.staticfiles.finders.DefaultStorageFinder",
]

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = [
    "django.template.loaders.filesystem.Loader",
#    "django.template.loaders.app_directories.Loader",
#    "django.template.loaders.eggs.Loader",
]

MIDDLEWARE_CLASSES = [
    "django.middleware.common.CommonMiddleware",
#    "django.contrib.sessions.middleware.SessionMiddleware",
#    "django.contrib.auth.middleware.AuthenticationMiddleware",
#    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "datazilla.webapp.urls"

TEMPLATE_DIRS = [
    path("datazilla/webapp/templates")
]

INSTALLED_APPS = [
    #"django.contrib.auth",
    #"django.contrib.contenttypes",
    #"django.contrib.sessions",
    #"django.contrib.sites",
    #"django.contrib.messages",
    "django.contrib.staticfiles",
    # Uncomment the next line to enable the admin:
    # "django.contrib.admin",
    # Uncomment the next line to enable admin documentation:
    # "django.contrib.admindocs",

    "datazilla.model",
    "datazilla.webapp.apps.datazilla",
    "datazilla.model",
]

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler"
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
    }
}

# Import app-engine specific settings, if appropriate
if USE_APP_ENGINE:
    from .appengine import *

# Import local settings to add to/override the above
try:
    from .local import *
except ImportError:
    pass

# Derived settings, whose values should vary with local settings:

TEMPLATE_DEBUG = DEBUG

# The URL static assets will be served at.
STATIC_URL = "/static/"

CACHES = {
   "default": {
      "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
      "LOCATION": DATAZILLA_MEMCACHED,
   }
}

if not USE_APP_ENGINE:
    DATABASES = {
        "default": {
            "ENGINE"   : "django.db.backends.mysql", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
            "NAME"     : DATAZILLA_DATABASE_NAME,          # Or path to database file if using sqlite3.
            "USER"     : DATAZILLA_DATABASE_USER,     # Not used with sqlite3.
            "PASSWORD" : DATAZILLA_DATABASE_PASSWORD, # Not used with sqlite3.
            "HOST"     : DATAZILLA_DATABASE_HOST,     # Set to empty string for localhost. Not used with sqlite3.
            "PORT"     : DATAZILLA_DATABASE_PORT,     # Set to empty string for default. Not used with sqlite3.
        }
    }

