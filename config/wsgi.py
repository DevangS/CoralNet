"""
WSGI config for this Django project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://django.readthedocs.io/en/1.3.X/howto/deployment/modwsgi.html
"""

import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'CoralNet.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

# Ensure any imports starting with 'CoralNet' will work
path = '/mnt'
if path not in sys.path:
    sys.path.append(path)
