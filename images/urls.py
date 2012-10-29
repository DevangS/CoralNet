from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^source/$', 'images.views.source_list', name="source_list"),
    url(r'^source/about/$', 'images.views.source_about', name="source_about"),
    url(r'^source/new/$', 'images.views.source_new', name="source_new"),
    url(r'^source/(?P<source_id>\d+)/$', 'images.views.source_main', name="source_main"),
    url(r'^source/(?P<source_id>\d+)/edit/$', 'images.views.source_edit', name="source_edit"),
    url(r'^source/(?P<source_id>\d+)/invite/$', 'images.views.source_invite', name="source_invite"),
    url(r'^image/(?P<image_id>\d+)/view/$', 'images.views.image_detail', name="image_detail"),
    url(r'^image/(?P<image_id>\d+)/edit/$', 'images.views.image_detail_edit', name="image_detail_edit"),

    # Consider moving this to annotations or upload, or else remove this if we're no longer using it.
    url(r'^source/(?P<source_id>\d+)/label_import/$', 'images.views.import_labels', name="label_import"),

    # Consider moving this into accounts, or messages, or a separate
    # 'sources' app if we decide to have such a thing.
    url(r'^invites_manage/$', 'images.views.invites_manage', name="invites_manage"),
)
