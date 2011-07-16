from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from images.forms import ImageSourceForm

def newsource(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ImageSourceForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('success/') # Redirect after POST
    else:
        form = ImageSourceForm() # An unbound form

    return render_to_response('images/newsource.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
        )


def newsource_success(request):
    return render_to_response('images/newsource_success.html')
