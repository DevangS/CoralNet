from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^invite/$', 'accounts.views.request_invite', name="request_invite"),
)