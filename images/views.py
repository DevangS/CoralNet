from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from images.models import Source
from images.forms import ImageSourceForm

def source_new(request):
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
            # Add a success message
            messages.success(request, 'Source successfully created.')
            return HttpResponseRedirect(reverse('source_main', args=[newSource.id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # An unbound form
        form = ImageSourceForm()

    # RequestContext needed for CSRF verification of POST form,
    # and to correctly get the path of the CSS file being used.
    return render_to_response('images/source_new.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
        )

def source_main(request, source_id):
    """
    Main page for a particular image source.
    """

    source = Source.objects.get(id=source_id)

    return render_to_response('images/source_main.html', {
        'source': source,
        },
        context_instance=RequestContext(request)
        )

def source_edit(request, source_id):
    """
    Edit an image source: name, visibility, location keys, etc.
    """

    source = Source.objects.get(id=source_id)

    if request.method == 'POST':

        # Cancel
        cancel = request.POST.get('cancel', None)
        if cancel:
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))

        # Submit
        form = ImageSourceForm(request.POST, instance=source)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Source successfully edited.')
            return HttpResponseRedirect(reverse('source_main', args=[source_id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Just reached this form page
        form = ImageSourceForm(instance=source)

    return render_to_response('images/source_edit.html', {
        'source': source,
        'editSourceForm': form,
        },
        context_instance=RequestContext(request)
        )
