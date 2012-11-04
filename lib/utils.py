# General utility functions and classes can go here.
#
# This file should eventually replace CoralNet/utils.py, because
# it's not always obvious how to import a file that's at the top
# level of a Django project (you have to refer to the project name).

from django.http import HttpResponse
from django.utils import simplejson


def JsonResponse(response):
    """
    Construct a JSON response to return from an Ajax views.
    Based on djcelery.views.JsonResponse.

    response - some data to convert to JSON and turn into an AJAX response.

    Example:
    return JsonResponse({'message': "Hello"})
    """
    return HttpResponse(simplejson.dumps(response), mimetype="application/json")