from django.shortcuts import render_to_response
from django.template import RequestContext

def newsource(request):
    return render_to_response('images/newsource.html')

    # When the user system's all up and running, uncomment this,
    # along with newsource.html's {% csrf_token %} tag:

    ## Need to use a RequestContext to implement our CSRF check
    #return render_to_response('images/newsource.html',
    #                          context_instance=RequestContext(request))

def newsource_success(request):
    return render_to_response('images/newsource_success.html')
