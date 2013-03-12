from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

from images.models import *


def map(request):

    return render_to_response('map/map.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        },
        context_instance=RequestContext(request)
    )