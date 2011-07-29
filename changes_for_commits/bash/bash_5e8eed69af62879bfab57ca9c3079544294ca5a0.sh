easy_install South

# Create South's migration-tracking tables.
# Note that after installing South, syncdb no longer operates on
# apps that South is tracking.
./manage.py syncdb

# Apply initial migrations for all apps that South is tracking.
# Assumes the database is created and empty.
# If it's not empty, then run "./manage.py migrate --fake" instead
./manage.py migrate
