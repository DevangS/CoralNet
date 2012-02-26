# Install django-reversion, for model version control.

easy_install django-reversion
./manage.py migrate reversion

# This can take a while.  On a netbook, on the order of 30 minutes
# to create initial versions for 18000 objects.
./manage.py createinitialrevisions
