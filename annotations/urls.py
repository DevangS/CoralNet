from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^labelsets/$', 'annotations.views.labelset_list', name="labelset_list"),
    url(r'^labels/$', 'annotations.views.label_list', name="label_list"),
    url(r'^labelsets/(?P<labelset_id>\d+)/$', 'annotations.views.labelset_main', name="labelset_main"),
    url(r'^labels/(?P<label_id>\d+)/$', 'annotations.views.label_main', name="label_main"),
    url(r'^labelset/new/$', 'annotations.views.labelset_new', name="labelset_new"),
    url(r'^labels/new/$', 'annotations.views.label_new', name="label_new"),
    url(r'^source/(?P<source_id>\d+)/annotate/(?P<image_id>\d+)/$', 'annotations.views.annotation_tool', name="annotation_tool"),
)