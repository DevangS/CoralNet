from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.utils import simplejson
from annotations.models import Annotation, Label
from CoralNet.decorators import visibility_required
from images.models import Source, Image
from visualization.forms import VisualizationSearchForm, ImageBatchActionForm
from visualization.utils import generate_patch_if_doesnt_exist


def image_search_args_to_queryset_args(searchDict):
    """
    Take the image search arguments directly from the visualization search form's
    form.cleaned_data, and return the search arguments in a format that can go into
    Image.objects.filter().

    Only the value1, ... valuen and the year in cleaned_data are processed.  label and
    page are ignored and not included in the returned dict.
    """

    searchArgs = dict([(k, searchDict[k]) for k in searchDict if searchDict[k] != ''])
    querysetArgs = dict()

    for k in searchArgs:
        if k.startswith('value'):
            querysetArgs['metadata__'+k+'__id'] = searchArgs[k]
        elif k == 'year':
            querysetArgs['metadata__photo_date__'+k] = int(searchArgs[k])

    return querysetArgs


def image_search_args_to_url_arg_str(searchDict):
    return '&'.join(['%s=%s' % (paramName, searchDict[paramName])
                     for paramName in searchDict
                     if searchDict[paramName]    # Don't include the arg if it's None or ''
                        and paramName != 'page'])


@visibility_required('source_id')
def visualize_source(request, source_id):
    """
    View for browsing through a source's images.
    """
    IMAGES_PER_PAGE = 20

    searchFormErrors = False
    source = get_object_or_404(Source, id=source_id)

    urlArgsStr = ''  # GET args in url format - for constructing prev page/next page links
    label = False
    imageArgs = dict()

    # Get image search filters, if any
    if request.GET:

        #form to select descriptors to sort images
        form = VisualizationSearchForm(source_id, request.GET)

        if form.is_valid():

            urlArgsStr = image_search_args_to_url_arg_str(form.cleaned_data)
            imageArgs = image_search_args_to_queryset_args(form.cleaned_data)

            label = form.cleaned_data['labels']

        else:
            searchFormErrors = True

    else:
        form = VisualizationSearchForm(source_id)


    # Perform selected actions, if any, on the images previously shown
    if request.POST:
        actionForm = ImageBatchActionForm(request.POST)

        if actionForm.is_valid():
            if actionForm.cleaned_data['action'] == 'delete':
                actionFormImageArgs = simplejson.loads(actionForm.cleaned_data['searchKeys'])
                imagesToDelete = Image.objects.filter(source=source, **actionFormImageArgs)

                for img in imagesToDelete:
                    pass
                    #img.delete()

                # Note that img.delete() just removes the image from the
                # database.  But the image objects are still there in the
                # imagesToDelete list (they just don't have primary keys anymore).
                messages.success(request, 'The %d selected images have been deleted.' % len(imagesToDelete))
    else:
        actionForm = ImageBatchActionForm(initial={'searchKeys': simplejson.dumps(imageArgs)})


    # Get the search results (all of them, not just on this page)
    # (This must happen after processing the action form, so that
    # images can be deleted/modified before we get search results.)

    errors = []
    if searchFormErrors:
        errors.append("There were errors in the search parameters.")
        images = []
        showPatches = False
    else:
        if not label:
            showPatches = False
            allSearchResults = Image.objects.filter(source=source, **imageArgs).order_by('-upload_date')
        else:
            showPatches = True
            patchArgs = dict([('image__'+k, imageArgs[k]) for k in imageArgs])

            #get all annotations for the source that contain the label
            annotations = Annotation.objects.filter(source=source, label=label, **patchArgs)

            # Placeholder the image patches with the annotation objects for now.
            # We'll actually get the patches when we know which page we're showing.
            allSearchResults = annotations

        if not allSearchResults:
            if request.GET:
                # No image results in this search
                errors.append("Sorry, no images matched your query")
            else:
                # No image results, and just got to the visualization page
                errors.append("Sorry, there are no images for this source yet. Please upload some.")

        paginator = Paginator(allSearchResults, IMAGES_PER_PAGE)

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

        if showPatches:

            # Get an image-patch for each result on the page.
            # Earlier we placeholdered the image patches with the annotation objects,
            # so we're iterating over those annotations now.
            for index, annotation in enumerate(images.object_list):

                patchPath = "data/annotations/" + str(annotation.id) + ".jpg"

                images.object_list[index] = dict(
                    fullImage=annotation.image,
                    patchPath=patchPath,
                    row=annotation.point.row,
                    col=annotation.point.column,
                    pointNum=annotation.point.point_number,
                )

                generate_patch_if_doesnt_exist(patchPath, annotation)

    return render_to_response('visualization/visualize_source.html', {
        'errors': errors,
        'form': form,
        'source': source,
        'images': images,
        'showPatches': showPatches,
        'searchParamsStr': urlArgsStr,
        'actionForm': actionForm,
        },
        context_instance=RequestContext(request)
    )
