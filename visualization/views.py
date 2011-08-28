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
            value2Index = request.GET.get('value2', '')
            value3Index = request.GET.get('value3', '')
            value4Index = request.GET.get('value4', '')
            value5Index = request.GET.get('value5', '')
            label = request.GET.get('label', '')

            value1List = Value1.objects.filter(source=source)
            value2List = Value2.objects.filter(source=source)
            value3List = Value3.objects.filter(source=source)
            value4List = Value4.objects.filter(source=source)
            value5List = Value5.objects.filter(source=source)

            if value1Index != "":
                kwargs['value1'] = value1List[int(value1Index)]
            if value2Index != "":
                kwargs['value2'] = value2List[int(value2Index)]
            if value3Index != "":
                kwargs['value3'] = value3List[int(value3Index)]
            if value4Index != "":
                kwargs['value4'] = value4List[int(value4Index)]
            if value5Index != "":
                kwargs['value5'] = value5List[int(value5Index)]

            #get all annotations for the source that contain the label
            #for each annotation
                #optional: check if annotation already has cropped image
                    #TODO: add the imagefield to annotation table, check image table for reference
                #get the annotation point
                #get the image
                #crop the image with the annotation point at center


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
