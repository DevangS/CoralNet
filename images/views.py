from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from images.forms import ImageSourceForm

def newsource(request):

    # We can get here one of two ways: either we just got to the form
    # page, or we just submitted the form.  If POST, we submitted; if
    # GET, we just got here.
    if request.method == 'POST':
        form = ImageSourceForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            return HttpResponseRedirect('success/') # Redirect after POST
    else:
        form = ImageSourceForm() # An unbound form

    # RequestContext needed for CSRF verification of POST form.
    return render_to_response('images/newsource.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
        )


def newsource_success(request):
    
    # RequestContext seems to be needed to correctly get the
    # path of the CSS file being used.
    return render_to_response('images/newsource_success.html',
        context_instance=RequestContext(request)
        )
