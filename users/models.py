from django.db import models
from userena.models import UserenaBaseProfile
import users

class UserProfile(UserenaBaseProfile):
    name = models.CharField(_('name'),
                            max_length=5)

AUTH_PROFILE_MODULE = users.UserProfile