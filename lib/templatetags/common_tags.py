# Custom template filters/tags need to live inside an app
# (http://www.b-list.org/weblog/2006/sep/10/django-tips-laying-out-application/),
# but some filters/tags are general and don't really belong in a specific
# app.  This file is for those general filters/tags.

import os.path
import re
from datetime import datetime, timedelta
from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import simplejson
from django.utils.safestring import mark_safe

register = template.Library()


def do_assignment_tag(parser, token, cls):
    # Uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    arg1, result_var_name = m.groups()
    return cls(arg1, result_var_name)


# Usage: {% get_form_media form as form_media %}
class GetFormMediaNode(template.Node):
    def __init__(self, form_context_var, result_var_name):
        self.form_context_var = template.Variable(form_context_var)
        self.result_var_name = result_var_name
    def render(self, context):
        form = self.form_context_var.resolve(context)
        context[self.result_var_name] = dict(js=form.media._js, css=form.media._css)
        return ''
@register.tag
def get_form_media(parser, token):
    return do_assignment_tag(parser, token, GetFormMediaNode)


# jsonify
#
# Pass a Django template variable through simplejson.dumps()
# and return the result.
# mark_safe() is used to prevent escaping of quote characters
# in the JSON (so they stay as quotes, and don't become &quot;).
#
# Usage: <script> ATH.init({{ labels|jsonify }}); </script>
#
# Basic idea from:
# http://djangosnippets.org/snippets/201/
@register.filter
def jsonify(object):
    return mark_safe(simplejson.dumps(object))


# Usage: {% set_maintenance_time "9:00 PM" as maintenance_time %}
class SetMaintenanceTimeNode(template.Node):
    def __init__(self, context_var, result_var_name):
        self.context_var = template.Variable(context_var)
        self.result_var_name = result_var_name

    def render(self, context):
        datetime_str = self.context_var.resolve(context)

        # Acceptable datetime formats.
        datetime_format_strs = dict(
            time = '%I:%M %p',                        # 12:34 PM
            day_and_time = '%b %d %I:%M %p',          # Jun 24 12:34 PM
            year_day_and_time = '%Y %b %d %I:%M %p',  # 2008 Jun 24 12:34 PM
        )
        datetime_obj = None
        now = datetime.now()

        # Parse the input, trying each acceptable datetime format.
        # Then infer the full date and time.
        for key, datetime_format_str in datetime_format_strs.iteritems():
            try:
                input = datetime.strptime(datetime_str, datetime_format_str)
                if key == 'time':
                    # Just the hour and minute were given.
                    # To find whether the intended day is yesterday,
                    # today, or tomorrow, assume that the admin meant a time
                    # within 12 hours (either way) from now.
                    datetime_obj = datetime(now.year, now.month, now.day,
                                            input.hour, input.minute)
                    if datetime_obj - now > timedelta(0.5):
                        datetime_obj = datetime_obj - timedelta(1)
                    elif now - datetime_obj > timedelta(0.5):
                        datetime_obj = datetime_obj + timedelta(1)
                elif key == 'day_and_time':
                    # The month, day, hour, and minute were given.
                    # To find whether the intended year is last year,
                    # this year, or next year, assume that the admin meant a
                    # date within ~half a year (either way) from now.
                    # This just handles the corner case if you're doing
                    # maintenance instead of celebrating the new year...
                    datetime_obj = datetime(now.year, input.month, input.day,
                        input.hour, input.minute)
                    if datetime_obj - now > timedelta(182.5):
                        datetime_obj = datetime(now.year-1, input.month, input.day,
                            input.hour, input.minute)
                    elif now - datetime_obj > timedelta(182.5):
                        datetime_obj = datetime(now.year+1, input.month, input.day,
                            input.hour, input.minute)
                elif key == 'year_day_and_time':
                    # The full date and time were given.
                    datetime_obj = input

                # We've got the date and time, so we're done.
                break

            except ValueError:
                continue

        context[self.result_var_name] = datetime_obj
        return ''
@register.tag
def set_maintenance_time(parser, token):
    return do_assignment_tag(parser, token, SetMaintenanceTimeNode)


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