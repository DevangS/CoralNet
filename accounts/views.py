# Create your views here.
from django.core.mail import send_mail, mail_admins
from django.core.mail.message import BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from accounts.forms import RequestInviteForm
from settings import DEFAULT_FROM_EMAIL

def request_invite(request):

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
               mail_admins('[CoralNet] Invite Requested', DEFAULT_FROM_EMAIL, message )
            except BadHeaderError:
                return HttpResponse('Invalid header found.')

            return HttpResponse('Your request was sent!')
        else:
            return HttpResponse('Make sure all fields are entered and valid.')
     else:
        form = RequestInviteForm()

     return render_to_response('accounts/request_invite.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
     )