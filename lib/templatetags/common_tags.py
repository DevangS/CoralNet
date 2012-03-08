# Custom template tags need to live inside an app
# (http://www.b-list.org/weblog/2006/sep/10/django-tips-laying-out-application/),
# but some template tags are general and don't really belong in a specific
# app.  This file is for those general tags.

import os.path
from django import template
from django.conf import settings
from django.contrib.staticfiles import finders

register = template.Library()


# versioned_static
#
# Prevent undesired browser caching of static files (CSS, JS, etc.)
# by adding a version string after the filename in the link/script element.
# The version string is the last-modified time of the file, which means
# the string changes (and thus, the browser re-fetches) if and only if
# the file has been modified.
#
# Usage: {% versioned_static "js/util.js" %}
# Example output: {{ STATIC_URL }}js/util.js?version=1035720937
@register.simple_tag
def versioned_static(relative_path):
    if settings.DEBUG:
        # Find file in development environment
        absolute_path = finders.find(relative_path)
    else:
        # Find file in production environment
        absolute_path = os.path.join(settings.STATIC_ROOT, relative_path)

    return '%s?version=%s' % (
        os.path.join(settings.STATIC_URL, relative_path),
        int(os.path.getmtime(absolute_path))
        )