from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #(r'', include('images.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('userena.urls')),
    (r'^messages/', include('userena.contrib.umessages.urls')),
    url(r'^$',
        direct_to_template,
        {'template': 'static/index.html'},
        name='index'),
    (r'^i18n/', include('django.conf.urls.i18n')),                   
   
    # Examples:
    # url(r'^$', 'CoralNet.views.home', name='home'),
    # url(r'^CoralNet/', include('CoralNet.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),


)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$',
         'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True, }),
)


