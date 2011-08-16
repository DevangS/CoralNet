from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from guardian.decorators import permission_required
from images.models import Source

@permission_required('source_admin', (Source, 'id', 'source_id'))
def visualize_source(request, source_id, value1_id, value2_id, value3_id, value4_id, value5_id):
    """
    View for browsing through a source's images.
    """

    source = get_object_or_404(Source, id=source_id)

    # TODO: Don't get all the images in a source,
    # just get the ones in the particular page that we want.
    # (e.g. page 1 has images 1-15, page 2 has images 16-30, etc.)
    all_images = source.get_all_images().order_by('-upload_date')
    paginator = Paginator(all_images, 20) # Show 25 contacts per page

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        images = paginator.page(page)
    except (EmptyPage, InvalidPage):
        images = paginator.page(paginator.num_pages)

    return render_to_response('visualization/visualize_source.html', {
        'source': source,
        'images': images,
        },
        context_instance=RequestContext(request)
        
        def source_select_form(request):
    return render_to_response('source_select_form.html')
