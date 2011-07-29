# easy_install of Sentry will also install three apps that it depends on:
# django-indexer, django-paging, and django-templatetag-sugar.
# You may get warnings during installation, such as
# "warning: no files found matching 'README.rst'" and
# "warning: no previously-included files matching '*~' found anywhere in distribution".
# These warnings don't seem to be a problem.

easy_install django-sentry
./manage.py migrate

# Navigate to <root>/sentry/ to see Sentry.  You can log in as a site admin.
# Set DEBUG = False to see the 500 error page when you get an error.
