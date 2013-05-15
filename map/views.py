from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

from annotations.models import *
from images.models import *


def map(request):

    # Get all sources that have both latitude and longitude specified.
    # (In other words, leave out the sources that have either of them blank.)
    # TODO: When we have hidden sources, don't count the hidden sources.
    map_sources_queryset = Source.objects.exclude(latitude='').exclude(longitude='')

    map_sources = []

    for source in map_sources_queryset:

        # If the source is public, include a link to the source main page.
        # Otherwise, don't include a link.
        if source.visibility == Source.VisibilityTypes.PUBLIC:
            source_url = reverse('source_main', args=[source.id])
            color = '00FF00'
        else:
            source_url = ''
            color = 'FF0000'

        try:
            latitude = str(source.latitude)
            longitude = str(source.longitude)
        except:
            latitude = 'invalid'
            longitude = 'invalid'

        map_sources.append(dict(
            description=source.description,
            latitude=latitude,
            longitude=longitude,
            name=source.name,
            color = color,
            num_of_images=str( Image.objects.filter(source=source).count() ),
            url=source_url,
        ))


    # TODO: When we have hidden sources, don't count the hidden sources.
    # TODO: Should we not count sources that don't have latitude/longitude
    #       specified?
    # TODO: Don't count images and annotations from sources that don't count.
    # TODO: Should we count robot annotations?

    total_sources = Source.objects.all().count()
    total_images = Image.objects.all().count()
    
    human_annotations = Point.objects.filter(image__status__annotatedByHuman=True).count()
    robot_annotations = Point.objects.filter(image__status__annotatedByRobot=True).count()
    total_annotations = human_annotations + robot_annotations




    return render_to_response('map/map.html', {
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'map_sources': map_sources,
        'total_sources': total_sources,
        'total_images': total_images,
        'total_annotations': total_annotations,
        'human_annotations': human_annotations,
        'robot_annotations' : robot_annotations,
        },
        context_instance=RequestContext(request)
    )
