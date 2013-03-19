from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

from annotations.models import *
from images.models import *


def map(request):

    # Get all sources that have both latitude and longitude specified.
    # (In other words, leave out the sources that have either of them blank.)
    # TODO: When we have hidden sources, don't count the hidden sources.
    map_sources_queryset = Source.objects.exclude(latitude='').exclude(longitude='')

    map_sources = [
        dict(
            description=source.description,
            latitude=str(source.latitude),
            longitude=str(source.longitude),
            name=source.name,
            num_of_images=str( Image.objects.filter(source=source).count() ),
        )
        for source in map_sources_queryset
    ]

    # TODO: When we have hidden sources, don't count the hidden sources.
    # TODO: Should we not count sources that don't have latitude/longitude
    #       specified?
    # TODO: Don't count images and annotations from sources that don't count.
    # TODO: Should we count robot annotations?

    total_sources = Source.objects.all().count()
    total_images = Image.objects.all().count()
    total_annotations = Annotation.objects.all().count()

    return render_to_response('map/map.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'map_sources': map_sources,
        'total_sources': total_sources,
        'total_images': total_images,
        'total_annotations': total_annotations,
        },
        context_instance=RequestContext(request)
    )