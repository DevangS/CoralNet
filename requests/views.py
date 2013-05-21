from django.core.mail import mail_admins
from django.core.mail.message import BadHeaderError
from django.http import HttpResponse, HttpRequest 
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from requests.forms import RequestInviteForm
from settings import DEFAULT_FROM_EMAIL 
from settings_2 import CAPTCHA_PRIVATE_KEY, CAPTCHA_PUBLIC_KEY
import urllib2, urllib

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
            response_field =  request.POST.get("recaptcha_response_field")
            challenge_field = request.POST.get("recaptcha_challenge_field") 
            
            try:
                client_ip = request.META['HTTP_X_FORWARDED_FOR']
            except:
                client_ip = request.META['REMOTE_ADDR']
            print client_ip

            message = 'Email: ' + email + '\n' + \
                      'Username: ' + username + '\n' + \
                      'Reason: ' + reason + '\n' + \
                      'affiliation: ' + affiliation + '\n' + \
                      'project_description: ' + project_description +'\n'+\
                      'how_did_you_hear_about_us: ' + how_did_you_hear_about_us + '\n'
            
            params = urllib.urlencode ({
              'privatekey': encode_if_necessary(CAPTCHA_PRIVATE_KEY),
              'remoteip' :  encode_if_necessary(client_ip),
              'challenge':  encode_if_necessary(challenge_field),
              'response' :  encode_if_necessary(response_field),
            })

            captcha_verify = urllib2.Request (
                url = "http://www.google.com/recaptcha/api/verify",
                data = params,
                headers = {
                    "Content-type": "application/x-www-form-urlencoded",
                    "User-agent": "CoralNet"
                }
            )
    
            httpresp = urllib2.urlopen (captcha_verify)
            return_values = httpresp.read ().splitlines ();
            httpresp.close();
            return_code = return_values [0]

            try:
               if (return_code == "true"):
                   mail_admins('User Account Requested', message )
                   messages.append('Your request was sent!')
               else:
                   messages.append('Invalid Captcha')
            except BadHeaderError:
                messages.append('Invalid header found.')

        else:
            messages.append('Make sure all fields are entered and valid.')
     else:
        form = RequestInviteForm()

     
     return render_to_response('requests/request_invite.html', {
        'messages': messages,
        'form': form,
        'public_key': CAPTCHA_PUBLIC_KEY,
        },
        context_instance=RequestContext(request)
     )


def encode_if_necessary(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return s



