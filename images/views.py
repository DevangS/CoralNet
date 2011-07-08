from django.shortcuts import render_to_response
from django.template import RequestContext

from images.models import Source

import datetime

def newsource(request):
    return render_to_response('images/newsource.html')

    # When the user system's all up and running, uncomment this,
    # along with newsource.html's {% csrf_token %} tag:

    ## Need to use a RequestContext to implement our CSRF check
    #return render_to_response('images/newsource.html',
    #                          context_instance=RequestContext(request))

def newsource_success(request):
    errorMessages = []
    sourceName = ''
    visibilitySetting = ''
    
    try:
        sourceName = request.GET['sourceName']
        if len(sourceName) == 0:
            raise ValueError
    except (KeyError, ValueError):
        errorMessages.append("Please enter a Source name.")

    try:
        visibilitySetting = request.GET['visibilitySetting']
    except KeyError:
        errorMessages.append("Please select a visibility setting.")

    if len(errorMessages) > 0:
        # Go back to New Source form.
        # (Include RequestContext parameter when we switch to POST forms)
        return render_to_response('images/newsource.html',{
            'messages': errorMessages,
        })

    s = Source(name=sourceName,
               visibility=visibilitySetting,
               create_date=datetime.datetime.now())
    s.save()
    return render_to_response('images/newsource_success.html')
