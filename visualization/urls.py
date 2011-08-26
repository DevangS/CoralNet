from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^(?P<source_id>\d+)/$', 'visualization.views.visualize_source', name="visualize_source"),
)
