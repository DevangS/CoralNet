from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.mail.message import BadHeaderError
from django.shortcuts import render_to_response
from django.template import RequestContext
from lib.forms import ContactForm
from lib import msg_consts

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
            subject = "Contact Us - {username} - {base_subject}".format(
                username=request.user.username,
                base_subject=contact_form.cleaned_data['subject'],
            )
            message = ("This email was sent using the Contact Us form.\n"
                       "\n"
                       "Username: {username}\n"
                       "User's email: {user_email}\n"
                       "\n"
                       "{base_message}").format(
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
                messages.error(request, 'Sorry, the email could not be sent. An invalid header was found.')

            # Stay on the same page, but put a message at the top of the page.
            messages.success(request, "Your email was sent!")
        else:
            messages.error(request, msg_consts.FORM_ERRORS)

    else: # GET
        contact_form = ContactForm()

    return render_to_response('lib/contact.html', {
        'contact_form': contact_form,
        },
        context_instance=RequestContext(request)
    )