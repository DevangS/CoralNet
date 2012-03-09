# Django settings for CoralNet project.
import settings_2
import os, sys
from django.conf.locale import en
import djcelery
djcelery.setup_loader()

abspath = lambda *p: os.path.abspath(os.path.join(*p))


PROJECT_ROOT = settings_2.PROJECT_ROOT

PROCESSING_ROOT = settings_2.PROCESSING_ROOT

USERENA_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, USERENA_MODULE_PATH)

DEBUG = settings_2.DEBUG

# TEMPLATE_DEBUG = True lets Sentry get template error info.  This
# won't reveal any error details to end users as long as DEBUG = False.
TEMPLATE_DEBUG = True

ADMINS = settings_2.ADMINS

MANAGERS = settings_2.MANAGERS

DATABASES = settings_2.DATABASES

# Default configurations to use when sending email
DEFAULT_FROM_EMAIL = settings_2.DEFAULT_FROM_EMAIL
SERVER_EMAIL = DEFAULT_FROM_EMAIL
#Default string to append in front of the subject of emails sent by the server
EMAIL_SUBJECT_PREFIX = '[CoralNet] '

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

ugettext = lambda s: s
LANGUAGES = (
    ('en', ugettext('English')),
    ('nl', ugettext('Dutch')),
    ('fr', ugettext('French')),
    ('pl', ugettext('Polish')),
    ('pt', ugettext('Portugese')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = abspath(PROJECT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# File uploading
ORIGINAL_IMAGE_DIR = 'data/original/'
LABEL_THUMBNAIL_DIR = 'label_thumbnails/'
FILE_UPLOAD_MAX_MEMORY_SIZE = settings_2.FILE_UPLOAD_MAX_MEMORY_SIZE

DOCUMENT_ROOT = abspath(PROJECT_ROOT, 'docs')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = settings_2.STATIC_ROOT

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
# (besides apps' "static/" subdirectories, which are automatically included)
STATICFILES_DIRS = (
    # Put strings here, like "/home/chtml/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # And remember to include a comma after the last element.

    # Project-wide static files
    abspath(PROJECT_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = settings_2.SECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

# The order of middleware classes is important!
# https://docs.djangoproject.com/en/1.3/topics/http/middleware/
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'userena.middleware.UserenaLocaleMiddleware',
    'sentry.client.middleware.Sentry404CatchMiddleware',

    # Put TransactionMiddleware after most non-cache middlewares that use the DB.
    # Any middleware specified after TransactionMiddleware will be
    # included in the same DB transaction that wraps the view function.
    # https://docs.djangoproject.com/en/1.3/topics/db/transactions/#tying-transactions-to-http-requests
    'django.middleware.transaction.TransactionMiddleware',

    # Put after TransactionMiddleware.
    # Model revisions needs to be part of transactions.
    'reversion.middleware.RevisionMiddleware',
)

ROOT_URLCONF = 'CoralNet.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    abspath(PROJECT_ROOT, 'templates')
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'userena',
    'userena.contrib.umessages',
    'guardian',
    'easy_thumbnails',
    'south',
    'reversion',
    'sentry',
    'sentry.client',
    'dajaxice',
    'dajax',
    'djcelery',
    'CoralNet.accounts',
    'CoralNet.images',
    'CoralNet.annotations',
    'CoralNet.visualization',
    'CoralNet.bug_reporting',
    'CoralNet.requests',
    'CoralNet.lib',
    'GChartWrapper.charts',
)


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

AUTHENTICATION_BACKENDS = (
    'userena.backends.UserenaAuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend', # this is default

)

#Django-guardian settings
ANONYMOUS_USER_ID = -1

# Other special user ids
IMPORTED_USER_ID = -2
ROBOT_USER_ID = -3

#Userena settings
LOGIN_REDIRECT_URL = '/images/source/'
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'
AUTH_PROFILE_MODULE = 'accounts.Profile'
USERENA_SIGNIN_REDIRECT_URL = LOGIN_REDIRECT_URL
USERENA_USE_MESSAGES = False
USERENA_LANGUAGE_FIELD = 'en'

# South settings: http://south.aeracode.org/docs/settings.html
SOUTH_MIGRATION_MODULES = {
    # Specify a nonexistent path like 'ignore' if an app has a migrations
    # folder in the default location and you want South to ignore it.

    # easy_thumbnails has migrations modules, but South has issues
    # getting to them because the easy_thumbnails egg is zip-safe
    # (as of version 1.0 alpha 17).
    'easy_thumbnails': 'ignore',
}

# Sentry settings: http://readthedocs.org/docs/sentry/en/latest/config/index.html
# SENTRY_TESTING enables usage of Sentry even when DEBUG = True
SENTRY_TESTING = True

# Dajaxice settings
DAJAXICE_MEDIA_PREFIX = "dajaxice"

#RabbitMQ hosts
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = settings_2.BROKER_USER
BROKER_PASSWORD = settings_2.BROKER_PASSWORD
BROKER_VHOST = settings_2.BROKER_VHOST

#Celery configuration
CELERYD_CONCURRENCY = settings_2.CELERYD_CONCURRENCY

# App URL bases
IMAGES_URL = '/images/'
ANNOTATIONS_URL = '/annotations/'
VISUALIZATION_URL = '/visualization/'
BUG_REPORTING_URL = '/feedback/'