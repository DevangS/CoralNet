from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext

from guardian.decorators import permission_required
from guardian.shortcuts import assign

from images.models import Source
from images.forms import ImageSourceForm

def source_list(request):
    """
    Page with a list of the user's Sources.
    Redirect to the About page if the user isn't logged in or doesn't have any Sources.
    """

    if request.user.is_authenticated():
        sources_of_user = Source.get_sources_of_user(request.user)
        
        if sources_of_user:
            return render_to_response('images/source_list.html', {
                'sources': sources_of_user,
                },
                context_instance=RequestContext(request)
            )

    return HttpResponseRedirect(reverse('source_about'))

def source_about(request):
    """
    Page that explains what Sources are and how to use them.
    """

    if request.user.is_authenticated():
        if Source.get_sources_of_user(request.user):
            user_status = 'has_sources'
        else:
            user_status = 'no_sources'
    else:
        user_status = 'anonymous'

    return render_to_response('images/source_about.html', {
        'user_status': user_status,
        },
        context_instance=RequestContext(request)
    )

@login_required
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
            # Save the source in the database
            newSource = form.save()
            # Grant permissions for this source
            assign('source_admin', request.user, newSource)
            # Add a success message
            messages.success(request, 'Source successfully created.')
            # Redirect to the source's main page
            return HttpResponseRedirect(reverse('source_main', args=[newSource.id]))
        else:
            # Show the form again, with error message
            messages.error(request, 'Please correct the errors below.')
    else:
        # An unbound form (empty form)
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

    source = get_object_or_404(Source, id=source_id)

    return render_to_response('images/source_main.html', {
        'source': source,
        },
        context_instance=RequestContext(request)
        )

# Must have the 'source_admin' permission for the Source whose id is source_id
@permission_required('source_admin', (Source, 'id', 'source_id'))
def source_edit(request, source_id):
    """
    Edit an image source: name, visibility, location keys, etc.
    """

    source = get_object_or_404(Source, id=source_id)

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
