from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from images.models import Source
from images.forms import ImageSourceForm

def newsource(request):

    # We can get here one of two ways: either we just got to the form
    # page, or we just submitted the form.  If POST, we submitted; if
    # GET, we just got here.
    if request.method == 'POST':
        form = ImageSourceForm(request.POST) # A form bound to the POST data
        
        if form.is_valid(): # All validation rules pass

            # Process form.cleaned_data:
            # Key n only makes sense if 1 through n-1 are specified
            data = form.cleaned_data
            if not data.has_key('key1'):
                del data['key2']
            if not data.has_key('key2'):
                del data['key3']
            if not data.has_key('key3'):
                del data['key4']
            if not data.has_key('key4'):
                del data['key5']
            form.cleaned_data = data

            form.save()
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
