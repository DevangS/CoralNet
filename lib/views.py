from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from lib.forms import ContactForm

@login_required
def contact(request):
    """
    Page with a contact form, which allows the user to send a general
    purpose email to the site admins.
    """
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)

        if contact_form.is_valid():
            # TODO: Send the email.
            return HttpResponseRedirect(reverse('contact_success'))
        else:
            messages.error(request, 'Please correct the errors below.')

    else: # GET
        contact_form = ContactForm()

    return render_to_response('lib/contact.html', {
        'contact_form': contact_form,
        },
        context_instance=RequestContext(request)
    )