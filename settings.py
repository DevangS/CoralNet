# Django settings for CoralNet project.
import settings_2
import os, sys
from django.conf.locale import en
import djcelery
djcelery.setup_loader()

abspath = lambda *p: os.path.abspath(os.path.join(*p))


PROJECT_ROOT = settings_2.PROJECT_ROOT

PROCESSING_ROOT = settings_2.PROCESSING_ROOT
TEST_PROCESSING_ROOT = settings_2.TEST_PROCESSING_ROOT

SLEEP_TIME_BETWEEN_IMAGE_PROCESSING = settings_2.SLEEP_TIME_BETWEEN_IMAGE_PROCESSING

USERENA_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, USERENA_MODULE_PATH)

DEBUG = settings_2.DEBUG

# TEMPLATE_DEBUG = True lets Sentry get template error info.  This
# won't reveal any error details to end users as long as DEBUG = False.
TEMPLATE_DEBUG = True

ADMINS = settings_2.ADMINS

MANAGERS = settings_2.MANAGERS

DATABASES = settings_2.DATABASES
EMAIL_HOST = 'localhost'
EMAIL_PORT = 9925
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
# TODO: Might be better to move this directory out of the repository.
MEDIA_ROOT = abspath(PROJECT_ROOT, 'media')

# Media Root to be used during unit tests.
# This directory is best kept out of the repository.
TEST_MEDIA_ROOT = settings_2.TEST_MEDIA_ROOT

# Directory for sample files to be uploaded during unit tests.
# This directory should be in the repository.
SAMPLE_UPLOADABLES_ROOT = abspath(PROJECT_ROOT, 'sample_uploadables')

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

# Define our project's installed apps separately from built-in and
# third-party installed apps.  This'll make it easier to define a
# custom test command that only runs our apps' tests.
# http://stackoverflow.com/a/2329425/859858
MY_INSTALLED_APPS = (
    'accounts',
    'images',
    'annotations',
    'visualization',
    'bug_reporting',
    'requests',
    'lib',
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
    'GChartWrapper.charts',
	'djsupervisor',
)
# Add MY_INSTALLED_APPS to INSTALLED_APPS, each with a 'CoralNet.' prefix.
INSTALLED_APPS += tuple(['CoralNet.'+app_name for app_name in MY_INSTALLED_APPS])


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

TEST_RUNNER = 'lib.test_utils.MyTestSuiteRunner'

# This is our own setting (not a standard Django setting) specifying the
# verbosity of print messages printed by our unit tests' code. Note that
# this is different from Django's test runner's verbosity setting, which
# relates to messages printed by the test runner code.
UNIT_TEST_VERBOSITY = settings_2.UNIT_TEST_VERBOSITY

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

    # easy_thumbnails has South migrations, but they're not that well
    # maintained; the project's GitHub page has several open issues
    # related to South migrations (as of easy_thumbnails 1.0.3).
    'easy_thumbnails': 'ignore',
}

# Sentry settings: http://readthedocs.org/docs/sentry/en/latest/config/index.html
# SENTRY_TESTING enables usage of Sentry even when DEBUG = True
SENTRY_TESTING = True

# South settings
SOUTH_TESTS_MIGRATE = settings_2.SOUTH_TESTS_MIGRATE

# Dajaxice settings
DAJAXICE_MEDIA_PREFIX = "dajaxice"
DAJAXICE_DEBUG = settings_2.DAJAXICE_DEBUG

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
