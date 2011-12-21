from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()

urlpatterns = patterns('',
    (r'^feedback/', include('bug_reporting.urls')),
    (r'^images/', include('images.urls')),
    (r'^visualization/', include('visualization.urls')),
    (r'^annotations/', include('annotations.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('userena.urls')),
    (r'^request/', include('accounts.urls')),
    (r'^messages/', include('userena.contrib.umessages.urls')),
    (r'^sentry/', include('sentry.web.urls')),
    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
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


# Custom server-error handler
def handler500(request):
    """
    500 error handler which includes ``request`` in the context.
    One use of this is to display a Sentry error ID on the 500 page.

    Templates: `500.html`
    Context: None
    """
    from django.template import Context, loader
    from django.http import HttpResponseServerError

    t = loader.get_template('500.html')
    return HttpResponseServerError(t.render(Context({
        'request': request,
        # It seems the user needs to be passed in manually for the
        # handler500 in particular - if this is mistaken, then change it
        'user': request.user,
    })))
