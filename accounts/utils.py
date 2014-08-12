from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from userena import settings as userena_settings
from userena.utils import get_protocol

def get_imported_user():
    return User.objects.get(pk=settings.IMPORTED_USER_ID)
def get_robot_user():
    return User.objects.get(pk=settings.ROBOT_USER_ID)
def get_alleviate_user():
    return User.objects.get(pk=settings.ALLEVIATE_USER_ID)

def is_imported_user(user):
    return user.pk == settings.IMPORTED_USER_ID
def is_robot_user(user):
    return user.pk == settings.ROBOT_USER_ID
def is_alleviate_user(user):
    return user.pk == settings.ALLEVIATE_USER_ID

def send_activation_email_with_password(userena_signup_obj, password):
    """
    Sends a activation email to the user, along with an
    automatically generated password that they need to log in.

    This function only exists because userena/models.py's
    UserenaSignup.send_activation_email() doesn't have a way to
    add custom context.
    """
    context= {'user': userena_signup_obj.user,
              'protocol': get_protocol(),
              'activation_days': userena_settings.USERENA_ACTIVATION_DAYS,
              'activation_key': userena_signup_obj.activation_key,
              'site': Site.objects.get_current(),
              'password': password}

    subject = render_to_string('userena/emails/activation_email_subject.txt',
        context)
    subject = ''.join(subject.splitlines())

    message = render_to_string('userena/emails/activation_email_message.txt',
        context)
    send_mail(subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [userena_signup_obj.user.email,])