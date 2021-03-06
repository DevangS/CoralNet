# Here's an example of what settings_2.py should look like.
#
# settings_2.py should *not* be tracked by the Git repository.
# settings_2.py is for settings that should be different between
# development copies and the production server.  (The main settings
# file, settings.py, *is* tracked by Git and will import from
# settings_2.py.)
#
# Remember to create your own settings_2.py, and keep an eye out for
# updates to this example file; make sure your settings_2.py has all
# the settings that this example file has.
#
# Please update this example file if you encounter any additional
# settings that should go in settings_2.py.

import os

abspath = lambda *p: os.path.abspath(os.path.join(*p))


PROJECT_ROOT = abspath(os.path.dirname(__file__))

SLEEP_TIME_BETWEEN_IMAGE_PROCESSING = 5 * 60 # 60*60 on the server, but shorter on the dev. machines

# Absolute filesystem path to the directory that will
# hold input and output files for image processing tasks.
# This directory is best kept out of the repository.
# Example: "/home/mysite_processing/"
PROCESSING_ROOT = abspath(PROJECT_ROOT, '../processing')

# Processing Root to be used during unit tests.
# This directory is best kept out of the repository.
TEST_PROCESSING_ROOT = abspath(PROJECT_ROOT, '../test_files/processing')

DEBUG = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'databaseNameGoesHere',                      # Or path to database file if using sqlite3.
        'USER': 'usernameGoesHere',                      # Not used with sqlite3.
        'PASSWORD': 'passwordGoesHere',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Default e-mail address to use for various automated correspondence from
# the site managers.
DEFAULT_FROM_EMAIL = 'webmaster@yourdomainhere'

# Media Root to be used during unit tests.
# This directory is best kept out of the repository.
TEST_MEDIA_ROOT = abspath(PROJECT_ROOT, '../test_files/media')

FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB

# When uploading images and annotations together, the annotation dict needs
# to be kept on disk temporarily until all the Ajax upload requests are done.
# This is the directory where the dict files will be kept.
SHELVED_ANNOTATIONS_DIR = abspath(PROJECT_ROOT, '../tmp/shelved_annotations')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# This is our own setting (not a standard Django setting) specifying the
# verbosity of print messages printed by our unit tests' code. Note that
# this is different from Django's test runner's verbosity setting, which
# relates to messages printed by the test runner code.
#
# 0 means the unit tests won't print any additional messages.
#
# 1 means the unit tests will print additional messages as extra confirmation
# that things worked.
#
# There is no 2 for now, unless we see a need for it later.
UNIT_TEST_VERBOSITY = 0

# South settings
#
# SOUTH_TESTS_MIGRATE:
# True to run all South migrations before running any unit tests.
# False to not run South migrations, and instead run normal syncdb
# to build the database tables before tests.  This is much, much
# faster, but if the project has important initial data created by
# South data migrations, then tests may fail.
SOUTH_TESTS_MIGRATE = False

# Dajaxice settings
#
# DAJAXICE_DEBUG: True means that dajaxice.core.js will be
# regenerated every time a page using dajaxice is loaded.
# False means that dajaxice.core.js can only be generated
# with manage.py generate_static_dajaxice.
DAJAXICE_DEBUG = True

#RabbitMQ hidden configs
BROKER_USER = "usernameGoesHere"
BROKER_PASSWORD = "passwordGoesHere"
BROKER_VHOST = "vhostGoesHere"

#Celery configuration
CELERYD_CONCURRENCY = 2

# Google Maps
GOOGLE_MAPS_API_KEY = 'Go to https://code.google.com/apis/console/ and get an API key'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'tg5t&4x9f8edmnhe)d55tkk$e-djc4m_q%=^xo%n-jipn&v&8j'

# captcha keys. You can use these ones
CAPTCHA_PRIVATE_KEY = "6Le_tuESAAAAABtnO8YTAIJa81IJ_TuVJ4-3S6SV" 
CAPTCHA_PUBLIC_KEY = "6Le_tuESAAAAAMbVRTS5Pu6GjrePGwnyUZNSoUzj"


