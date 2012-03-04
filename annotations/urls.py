from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^labels/$', 'annotations.views.label_list', name="label_list"),
    url(r'^labels/(?P<label_id>\d+)/$', 'annotations.views.label_main', name="label_main"),
    url(r'^labels/new/$', 'annotations.views.label_new', name="label_new"),
    url(r'^labelsets/$', 'annotations.views.labelset_list', name="labelset_list"),
    url(r'^source/(?P<source_id>\d+)/labelset/$', 'annotations.views.labelset_main', name="labelset_main"),
    url(r'^source/(?P<source_id>\d+)/labelset/new/$', 'annotations.views.labelset_new', name="labelset_new"),
    url(r'^source/(?P<source_id>\d+)/labelset/edit/$', 'annotations.views.labelset_edit', name="labelset_edit"),
    url(r'^source/(?P<source_id>\d+)/annotate/(?P<image_id>\d+)/$', 'annotations.views.annotation_tool', name="annotation_tool"),
    url(r'^source/(?P<source_id>\d+)/annotation_history/(?P<image_id>\d+)/$', 'annotations.views.annotation_history', name="annotation_history"),
)