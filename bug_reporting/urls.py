from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'$', 'bug_reporting.views.feedback_form', name="feedback_form"),
)
