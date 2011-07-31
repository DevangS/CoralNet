# Django settings for CoralNet project.
import os, sys
from django.conf.locale import en

abspath = lambda *p: os.path.abspath(os.path.join(*p))
PROJECT_ROOT = abspath(os.path.dirname(__file__))
USERENA_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, USERENA_MODULE_PATH)

DEBUG = True

# TEMPLATE_DEBUG = True lets Sentry get template error info.  This
# won't reveal any error details to end users as long as DEBUG = False.
TEMPLATE_DEBUG = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'coralnet',                      # Or path to database file if using sqlite3.
        'USER': 'django',                      # Not used with sqlite3.
        'PASSWORD': 'djangor0cks',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

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

DOCUMENT_ROOT = abspath(PROJECT_ROOT, 'docs')


ADMIN_MEDIA_PREFIX = '/media/admin/'
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

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
SECRET_KEY = 'tg5t&4x9f8edmnhe)d55tkk$e-djc4m_q%=^xo%n-jipn&v&8j'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
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

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'userena.middleware.UserenaLocaleMiddleware',
    'sentry.client.middleware.Sentry404CatchMiddleware',
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
    'sentry',
    'sentry.client',
    'CoralNet.accounts',
    'CoralNet.images',
    'CoralNet.annotations',
    'CoralNet.visualization',
    'CoralNet.bug_reporting',
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

#Userena settings
LOGIN_REDIRECT_URL = '/accounts/%(username)s/'
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'
AUTH_PROFILE_MODULE = 'accounts.Profile'
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

# App URL bases
IMAGES_URL = '/images/'
ANNOTATIONS_URL = '/annotations/'
VISUALIZATION_URL = '/visualization/'
BUG_REPORTING_URL = '/feedback/'


