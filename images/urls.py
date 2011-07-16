from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    (r'^source/new/$', 'images.views.newsource'),
    (r'^source/(?P<source_id>\d+)/$', 'images.views.source_main'),
)
