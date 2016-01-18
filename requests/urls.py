from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^accounts/$', 'requests.views.request_invite', name="request_account"),
    url(r'^accounts/confirm/$', 'requests.views.request_invite_confirm', name="request_account_confirm"),
)