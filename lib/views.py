from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.mail.message import BadHeaderError
from django.shortcuts import render_to_response
from django.template import RequestContext
from lib.forms import ContactForm
from lib import msg_consts, str_consts
from lib.utils import get_map_sources, get_random_public_images
from images.models import Image, Source
from annotations.models import Annotation

def contact(request):
    """
    Page with a contact form, which allows the user to send a general
    purpose email to the site admins.
    """
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)

        if contact_form.is_valid():
            # Set up the subject and message.
            subject = str_consts.CONTACT_EMAIL_SUBJECT_FMTSTR.format(
                username=request.user.username,
                base_subject=contact_form.cleaned_data['subject'],
            )
            message = str_consts.CONTACT_EMAIL_MESSAGE_FMTSTR.format(
                username=request.user.username,
                user_email=request.user.email,
                base_message=contact_form.cleaned_data['message'],
            )

            # Send the mail.
            try:
                mail_admins(
                    subject=subject,
                    message=message,
                )
            except BadHeaderError:
                messages.error(request, "Sorry, the email could not be sent. An invalid header was found.")
            else:
                messages.success(request, msg_consts.CONTACT_EMAIL_SENT)
        else:
            messages.error(request, msg_consts.FORM_ERRORS)

    else: # GET
        contact_form = ContactForm()

    return render_to_response('lib/contact.html', {
        'contact_form': contact_form,
        },
        context_instance=RequestContext(request)
    )

def index(request):
    """
    This view renders the front page.
    """

    # Here we get the map sources
    map_sources = get_map_sources()

    # and here we get 5 random public images
    images = get_random_public_images()

    # Gather some stats
    total_sources = Source.objects.all().count()
    total_images = Image.objects.all().count()
    total_annotations = Annotation.objects.all().count()

    return render_to_response('lib/index.html', {
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'map_sources': map_sources,
            'total_sources': total_sources,
            'total_images': total_images,
            'total_annotations': total_annotations,
            'images': images
        },
        context_instance=RequestContext(request)
    )

def index2(request):
    """
    This view renders the front page.
    """

    # Here we get the map sources
    map_sources = get_map_sources()

    # and here we get 5 random public images
    images = get_random_public_images()

    # Gather some stats
    total_sources = Source.objects.all().count()
    total_images = Image.objects.all().count()
    total_annotations = Annotation.objects.all().count()

    return render_to_response('lib/index2.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'map_sources': map_sources,
        'total_sources': total_sources,
        'total_images': total_images,
        'total_annotations': total_annotations,
        'images': images
    },
        context_instance=RequestContext(request)
    )