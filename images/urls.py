from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^source/new/$', 'images.views.source_new', name="source_new"),
    url(r'^source/(?P<source_id>\d+)/$', 'images.views.source_main', name="source_main"),
    url(r'^source/(?P<source_id>\d+)/edit/$', 'images.views.source_edit', name="source_edit"),
)
