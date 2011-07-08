from django.conf.urls.defaults import *  # 404, 500, patterns, include, url

urlpatterns = patterns('',
    (r'^newsource/$', 'images.views.newsource'),
    (r'^newsource/success/$', 'images.views.newsource_success'),
)
