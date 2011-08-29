from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^source/$', 'images.views.source_list', name="source_list"),
    url(r'^source/about/$', 'images.views.source_about', name="source_about"),
    url(r'^source/new/$', 'images.views.source_new', name="source_new"),
    url(r'^source/(?P<source_id>\d+)/$', 'images.views.source_main', name="source_main"),
    url(r'^source/(?P<source_id>\d+)/edit/$', 'images.views.source_edit', name="source_edit"),
    url(r'^source/(?P<source_id>\d+)/upload/$', 'images.views.image_upload', name="image_upload"),
    url(r'^source/(?P<source_id>\d+)/view/(?P<image_id>\d+)/$', 'images.views.image_detail', name="image_detail"),
    url(r'^source/(?P<source_id>\d+)/edit/(?P<image_id>\d+)/$', 'images.views.image_detail_edit', name="image_detail_edit"),
    url(r'^source/(?P<source_id>\d+)/label_import/$', 'images.views.import_labels', name="label_import"),
    #(r'^source/importAnnotations/(?P<source_id>\d+)/(?P<filename>\w+)/$', 'images.views.import_annotations'),

    url(r'^source/(?P<source_id>\d+)/annotation_import/$', 'images.views.annotation_import', name="annotation_import"),
)
