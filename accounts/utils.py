from django.conf import settings
from django.contrib.auth.models import User

def get_imported_user():
    return User.objects.get(pk=settings.IMPORTED_USER_ID)

def get_robot_user():
    return User.objects.get(pk=settings.ROBOT_USER_ID)
