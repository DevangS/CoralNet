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
    visibilityStr = ''
    
    try:
        sourceName = request.GET['sourceName'].strip()
        # After stripping leading/trailing spaces, must be nonempty
        if len(sourceName) == 0:
            raise ValueError
    except (KeyError, ValueError):
        errorMessages.append("Please enter a Source name.")

    try:
        visibilityStr = request.GET['visibilitySetting']
    except KeyError:
        errorMessages.append("Please select a visibility setting.")

    # Location keys.
    keys = {}
    for keyNum in ['key1', 'key2', 'key3', 'key4', 'key5']:
        try:
            key = request.GET[keyNum].strip()
            # After stripping leading/trailing spaces, must be nonempty
            if len(key) == 0:
                raise ValueError
            else:
                keys[keyNum] = key

        except (KeyError, ValueError):
            break    # Blank key field, so we're done taking keys.

    # Longitude, Latitude.
    try:
        longitude = request.GET['longitude'].strip()
    except KeyError:
        longitude = None

    try:
        latitude = request.GET['latitude'].strip()
    except KeyError:
        latitude = None


    if len(errorMessages) > 0:
        # Go back to New Source form.
        # (Include RequestContext parameter when we switch to POST forms)
        return render_to_response('images/newsource.html',{
            'messages': errorMessages,
        })

    s = Source(name=sourceName,
               visibility=Source.visibilityStrToCode[visibilityStr],
               create_date=datetime.datetime.now(),
               longitude=longitude,
               latitude=latitude,
               **keys)
    s.save()
    return render_to_response('images/newsource_success.html')
