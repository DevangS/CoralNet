from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.mail.message import BadHeaderError
from django.shortcuts import render_to_response
from django.template import RequestContext
from lib.forms import ContactForm
from lib import msg_consts, str_consts

@login_required
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