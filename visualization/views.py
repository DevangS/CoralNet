from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from guardian.decorators import permission_required
from annotations.models import Annotation
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Image
from visualization.forms import VisualizationSearchForm

@permission_required('source_admin', (Source, 'id', 'source_id'))
def visualize_source(request, source_id):
    """
    View for browsing through a source's images.
    """
    kwargs = {
        #this will contain the parameters to filter the images by
        #that way the filter args can be dynamically generated if
        #all possible values are not filled
    }

    source = get_object_or_404(Source, id=source_id)
    kwargs['source'] = source

    if request.GET:
        #form to select descriptors to sort images
        form = VisualizationSearchForm(source_id, request.GET)
        if form.is_valid():
            value1Index = request.GET.get('value1', '')
            value1List = Value1.objects.filter(source=source)
            if value1Index != "":
                kwargs['value1'] = value1List[int(value1Index)]

            #label = request.GET.label
    else:
        form = VisualizationSearchForm(source_id)


     #   if label != "":
      #      Annotation.objects.filter(label=label, source=source)
       #     for image in Annotation.objects:
        #        image.name
    # just get the ones in the particular page that we want.
    # (e.g. page 1 has images 1-15, page 2 has images 16-30, etc.)
    all_images = Image.objects.filter(**kwargs).order_by('-upload_date')
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
        'form': form,
        'source': source,
        'images': images,
        },
        context_instance=RequestContext(request)
        
    )

    """
    def source_select_form(request):
        return render_to_response('source_select_form.html')
    """