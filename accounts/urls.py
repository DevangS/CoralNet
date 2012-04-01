# This urls file has:
# - userena's urlpatterns
# - our urlpatterns which override userena's urlpatterns
# - other accounts-related urls

from django.conf.urls.defaults import patterns, url, include
from accounts import views as accounts_views
from userena import views as userena_views

urlpatterns = patterns('',

    # Overriding userena urlpatterns
    url(r'^signin/$', userena_views.signin,
        {'template_name': 'userena/signin_form.html'},
        name='signin'),
    url(r'^signup/$', accounts_views.user_add,
        name='signup'),

    # Include userena urls after our urls, so ours take precedence
    (r'', include('userena.urls')),
)
