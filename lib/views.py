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
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from annotations.models import Point

def contact(request):
    """
    Page with a contact form, which allows the user to send a general
    purpose email to the site admins.
    """
    if request.method == 'POST':
        contact_form = ContactForm(request.user, request.POST)

        if contact_form.is_valid():
            # Set up the subject and message.
            if request.user.is_authenticated():
                username = request.user.username,
                base_subject=contact_form.cleaned_data['subject']
                user_email=request.user.email
                base_message=contact_form.cleaned_data['message']
            else:
                username = "[A guest]"
                base_subject = contact_form.cleaned_data['subject']
                user_email = contact_form.cleaned_data['email']
                base_message = contact_form.cleaned_data['message']

            subject = str_consts.CONTACT_EMAIL_SUBJECT_FMTSTR.format(
                username=username,
                base_subject=base_subject,
            )
            message = str_consts.CONTACT_EMAIL_MESSAGE_FMTSTR.format(
                username=username,
                user_email=user_email,
                base_message=base_message,
            )

            # Send the mail.
            try:
                mail_admins(
                    subject=subject,
                    message=message,
                )
            except BadHeaderError:
                messages.error(
                    request,
                    "Sorry, the email could not be sent. It didn't pass a security check."
                )
            else:
                messages.success(request, msg_consts.CONTACT_EMAIL_SENT)
                return HttpResponseRedirect(reverse('index'))
        else:
            messages.error(request, msg_consts.FORM_ERRORS)

    else: # GET
        contact_form = ContactForm(request.user)

    return render_to_response('lib/contact.html', {
        'contact_form': contact_form,
        },
        context_instance=RequestContext(request)
    )

def index(request):
    """
    This view renders the front page.
    """

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('source_list'))

    # Here we get the map sources
    map_sources = get_map_sources()

    list_thumbnails = []
    # Here we get a list of a list of images, these will be displayed
    # within each of the description windows.
    # the latest images source will not be passed into the javascript functions
    for source in map_sources:
        list_thumbnails.append((source["latest_images"],source["id"]))
        del source["latest_images"]

    # and here we get 5 random public images
    images = get_random_public_images()

    # Gather some stats
    total_sources = Source.objects.all().count()
    total_images = Image.objects.all().count()
    human_annotations = Point.objects.filter(image__status__annotatedByHuman=True).count()
    robot_annotations = Point.objects.filter(image__status__annotatedByRobot=True).count()
    total_annotations = human_annotations + robot_annotations

    return render_to_response('lib/index.html', {
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
            'map_sources': map_sources,
            'total_sources': total_sources,
            'total_images': total_images,
            'total_annotations': total_annotations,
            'human_annotations': human_annotations,
            'robot_annotations' : robot_annotations,
            'images': images,
            'list_thumbnails': list_thumbnails,
        },
        context_instance=RequestContext(request)
    )
