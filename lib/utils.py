# General utility functions and classes can go here.
#
# This file should eventually replace CoralNet/utils.py, because
# it's not always obvious how to import a file that's at the top
# level of a Django project (you have to refer to the project name).

import json

from django.http import HttpResponse
from images.models import Source, Image
from django.core.urlresolvers import reverse
from random import choice


def JsonResponse(response):
    """
    Construct a JSON response to return from an Ajax views.
    Based on djcelery.views.JsonResponse.

    response - some data to convert to JSON and turn into an AJAX response.

    Example:
    return JsonResponse({'message': "Hello"})
    """
    return HttpResponse(json.dumps(response), mimetype="application/json")

def get_map_sources():
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

        all_images = source.get_all_images()
        latest_images = all_images.order_by('-upload_date')[:6]


        map_sources.append(dict(
            description=source.description,
            affiliation=source.affiliation,
            latitude=latitude,
            longitude=longitude,
            name=source.name,
            color = color,
            num_of_images=str( Image.objects.filter(source=source).count() ),
            url=source_url,
            latest_images=latest_images,
            id=source.id
        ))


        # TODO: When we have hidden sources, don't count the hidden sources.
        # TODO: Should we not count sources that don't have latitude/longitude
        #       specified?
        # TODO: Don't count images and annotations from sources that don't count.
        # TODO: Should we count robot annotations?
    return map_sources

def get_random_public_images():
    """
    This will return a list of 5 random images that are from public sources only.
    These will be displayed on the front page to be seen in all their glory
    """
    public_sources_list = Source.get_public_sources()

    # return empty list if no public sources
    if len(public_sources_list) == 0:
        return public_sources_list

    random_source_list = []
    random_image_list = []

    # get 5 random public sources
    for i in range(5):
        random_source = choice(public_sources_list)
        random_source_list.append(random_source)

    # get a random image from each randomly chosen public source
    for source in random_source_list:
        all_images = source.get_all_images()

        if len(all_images) == 0:
            continue

        random_image = choice(all_images)
        random_image_list.append(random_image)

    return random_image_list
