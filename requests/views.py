from django.core.mail import mail_admins
from django.core.mail.message import BadHeaderError
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from requests.forms import RequestInviteForm
from settings import DEFAULT_FROM_EMAIL

def request_invite(request):

     messages = []

     if request.method == 'POST':
        form = RequestInviteForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data.pop('email')
            username = form.cleaned_data.pop('username')
            reason = form.cleaned_data.pop('reason')

            message = 'Email: ' + email + '\n' + \
                      'Username: ' + username + '\n' + \
                      'Reason: ' + reason + '\n'

            try:
               mail_admins('[CoralNet] Invite Requested', message )
            except BadHeaderError:
                messages.append('Invalid header found.')

            messages.append('Your request was sent!')
        else:
            messages.append('Make sure all fields are entered and valid.')
     else:
        form = RequestInviteForm()

     return render_to_response('requests/request_invite.html', {
        'messages': messages,
        'form': form,
        },
        context_instance=RequestContext(request)
     )