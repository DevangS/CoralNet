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
            affiliation = form.cleaned_data.pop('affiliation')
            project_description = form.cleaned_data.pop('project_description')
            how_did_you_hear_about_us = form.cleaned_data.pop('how_did_you_hear_about_us')

            message = 'Email: ' + email + '\n' + \
                      'Username: ' + username + '\n' + \
                      'Reason: ' + reason + '\n' + \
                      'affiliation: ' + affiliation + '\n' + \
                      'project_description: ' + project_description +'\n'+\
                      'how_did_you_hear_about_us: ' + how_did_you_hear_about_us + '\n'
            try:
               mail_admins('User Account Requested', message )
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
