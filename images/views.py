from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from images.models import Source
from images.forms import ImageSourceForm

def newsource(request):
    """
    Page with the form to create a new Image Source.
    """

    # We can get here one of two ways: either we just got to the form
    # page, or we just submitted the form.  If POST, we submitted; if
    # GET, we just got here.
    if request.method == 'POST':
        # A form bound to the POST data
        form = ImageSourceForm(request.POST)

        # is_valid() calls our ModelForm's clean() and checks validity
        if form.is_valid():
            newSource = form.save()
            return HttpResponseRedirect('../' + str(newSource.id) + '/')
    else:
        # An unbound form
        form = ImageSourceForm()

    # RequestContext needed for CSRF verification of POST form,
    # and to correctly get the path of the CSS file being used.
    return render_to_response('images/newsource.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
        )


def source_main(request, source_id):
    """
    Main page for a particular image source.
    """

    source = Source.objects.get(id=source_id)
    return render_to_response('images/source_main.html',
        {'source': source},
        context_instance=RequestContext(request)
        )
