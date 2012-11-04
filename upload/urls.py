from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    url(r'^source/(?P<source_id>\d+)/upload/$', 'upload.views.image_upload', name="image_upload"),
    url(r'^source/(?P<source_id>\d+)/upload_preview_ajax/$', 'upload.views.image_upload_preview_ajax', name="image_upload_preview_ajax"),
    url(r'^source/(?P<source_id>\d+)/annotation_file_process_ajax/$', 'upload.views.annotation_file_process_ajax', name="annotation_file_process_ajax"),
    url(r'^source/(?P<source_id>\d+)/upload_ajax/$', 'upload.views.image_upload_ajax', name="image_upload_ajax"),
    #url(r'^source/(?P<source_id>\d+)/ajax_upload_progress/$', 'upload.views.ajax_upload_progress', name="ajax_upload_progress"),
)
