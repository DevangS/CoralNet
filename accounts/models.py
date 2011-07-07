from django.db import models
from django.utils.translation import ugettext_lazy as _

from userena.models import UserenaLanguageBaseProfile

class Profile(UserenaLanguageBaseProfile):
    first_name = models.CharField(_('first name'), max_length=255, blank=True)
    last_name = models.CharField(_('last name'), max_length=255, blank=True)
    website = models.URLField(_('website'), blank=True, verify_exists=True)
    location =  models.CharField(_('location'), max_length=255, blank=True)
    about_me = models.TextField(_('about me'), blank=True)
