import csv
import json
import urllib
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from accounts.utils import get_robot_user
from annotations.models import Annotation, Label, LabelSet, LabelGroup
from decorators import source_visibility_required, source_permission_required
from images.models import Source, Image
from lib.utils import JsonResponse
from visualization.forms import BrowseSearchForm, StatisticsSearchForm, ImageBatchDeleteForm, ImageSpecifyForm, ImageBatchDownloadForm
from visualization.utils import generate_patch_if_doesnt_exist
from GChartWrapper import *
from upload.forms import MetadataForm, CheckboxForm
from django.forms.formsets import formset_factory
from django.utils.functional import curry
from numpy import array, zeros, sum, array_str, rank, linalg, logical_and, newaxis, float32, vectorize
from images.tasks import *

# TODO: Move to utils
def image_search_args_to_queryset_args(searchDict, source):
    """
    Take the image search arguments directly from the visualization search form's
    form.cleaned_data, and return the search arguments in a format that can go into
    Image.objects.filter().

    Only the value1, ... valuen and the year in cleaned_data are processed.  label and
    page, if present, are ignored and not included in the returned dict.
    """

    searchArgs = dict([(k, searchDict[k]) for k in searchDict if searchDict[k] != ''])
    querysetArgs = dict()

    for k in searchArgs:
        if k.startswith('value'):
            querysetArgs['metadata__'+k+'__id'] = searchArgs[k]
        elif k == 'year':
            querysetArgs['metadata__photo_date__'+k] = int(searchArgs[k])


    return querysetArgs

@source_visibility_required('source_id')
def visualize_source(request, source_id):
    """
    View for browsing through a source's images.
    """
    ITEMS_PER_PAGE = 20

    errors = []
    source = get_object_or_404(Source, id=source_id)
    metadata_view_available = request.user.has_perm(Source.PermTypes.EDIT.code, source)


    # This is used to create a formset out of the metadataForm. I need to do this
    # in order to pass in the source id.
    # From http://stackoverflow.com/a/624013
    metadataFormSet = formset_factory(MetadataForm)
    metadataFormSet.form = staticmethod(curry(MetadataForm, source_id=source_id))
    # There is a separate form that controls the checkboxes.
    checkboxFormSet = formset_factory(CheckboxForm)


    # Based on submitted GET/POST data, find the following:
    # - Which view mode we're showing
    # - Which images we're showing (if image/meta mode), or
    #   filtering the patches by (if patch mode)
    # - Other parameters


    # Defaults

    # Search form to show on the page
    search_form = BrowseSearchForm(source_id, metadata_view_available)

    # GET args in url format - for constructing prev page/next page links
    urlArgsStr = ''

    # View mode to show the Browse page in
    page_view = 'images'
    # (Patch mode only) the label we want to see patches of
    label = ''
    # (Patch mode only) show patches annotated by human, by machine, or by either one
    annotated_by = 'human'

    image_specify_form = ImageSpecifyForm(
        dict(
            specify_method='search_keys',
            specify_str=json.dumps(dict()),  # No filters, just get all images
        ),
        source=source,
    )


    if request.POST and 'image_specify_form_from_upload' in request.POST:

        # Coming from the upload page.

        # Let the user edit the metadata of the images they just uploaded.
        page_view = 'metadata'

        # Make the search form's page_view field value accurate.
        search_form = BrowseSearchForm(
            source_id, metadata_view_available,
            initial=dict(page_view=page_view),
        )

        # We expect the upload page to properly fill in an ImageSpecifyForm
        # with the image ids.
        image_specify_form = ImageSpecifyForm(request.POST, source=source)

        # Defaults on everything else

    elif request.GET:

        # Search form submitted OR
        # a URL with GET parameters was entered.

        submitted_search_form = BrowseSearchForm(
            source_id,
            metadata_view_available,
            request.GET,
        )

        if submitted_search_form.is_valid():

            # Have the search form on the page start with the values
            # submitted in this search.
            search_form = submitted_search_form

            # Some search form parameters are used for things other than image
            # filtering. Get these parameters.
            #
            # If any of these parameters are u'', then that parameter wasn't
            # submitted. Don't let that '' override the default value.
            if search_form.cleaned_data['page_view'] != u'':
                page_view = search_form.cleaned_data['page_view']
            if search_form.cleaned_data['label'] != u'':
                label = search_form.cleaned_data['label']
            if search_form.cleaned_data['annotated_by'] != u'':
                annotated_by = search_form.cleaned_data['annotated_by']

            # We're going to serialize this cleaned_data and give it
            # to an ImageSpecifyForm. A bit of cleanup to do first though.

            # The Label object isn't serializable, so avoid an error by
            # popping off this key first.
            search_form.cleaned_data.pop('label')

            if page_view == 'patches':
                # If in patch mode, the image_status filter doesn't apply.
                # Pop off this filter to make sure the ImageSpecifyForm
                # doesn't use it.
                search_form.cleaned_data.pop('image_status')

            # Give the search form data to the ImageSpecifyForm. Note that
            # with the exception of the above parameters, any parameters
            # not used for filtering images will just be ignored and won't cause problems.
            image_specify_form = ImageSpecifyForm(
                dict(
                    specify_method='search_keys',
                    specify_str=json.dumps(search_form.cleaned_data),
                ),
                source=source,
            )

        else:

            messages.error(request, 'Error: invalid search parameters.')

            # Use the defaults

    else:

        # Just got to this page via a link, with no GET parameters in the URL.

        # Use the defaults
        pass


    image_results = []
    delete_form = None
    download_form = None

    if image_specify_form.is_valid():

        image_results = image_specify_form.get_images()

        # Create image delete and image download forms if they're supposed
        # to be displayed on the page.
        #
        # Give the forms the same stuff as the image specify form, so they
        # know which images to operate on.
        if page_view == 'images':

            if request.user.has_perm(Source.PermTypes.EDIT.code, source):

                delete_form = ImageBatchDeleteForm(
                    image_specify_form.data,
                    source=source,
                )

            if request.user.has_perm(Source.PermTypes.VIEW.code, source):

                download_form = ImageBatchDownloadForm(
                    image_specify_form.data,
                    source=source,
                )

    else:

        errors.append("Error: something went wrong with this image search.")


    # Get the search results (all of them, not just on this page).

    if page_view == 'images' or page_view == 'metadata':

        # We'll display the images on the page. Sort them by image id
        # (highest id first).
        all_items = image_results.order_by('-pk')

    else:  # patches

        # Get the annotations in the source that:
        # - contain the label
        # - meet the "annotated_by" constraint
        #
        # And get the annotations in random order.
        #
        # Performance consideration: image__in=<queryset> might be slow in
        # MySQL. If in doubt, test/benchmark it.
        # https://docs.djangoproject.com/en/1.5/ref/models/querysets/#in
        annotations = Annotation.objects.filter(source=source, label=label, image__in=image_results).order_by('?')

        if annotated_by == 'either':
            # No further filtering needed
            pass
        elif annotated_by == 'machine':
            annotations = annotations.filter(user=get_robot_user())
        else:  # 'human'
            annotations = annotations.exclude(user=get_robot_user())

        # Placeholder the image patches with the Annotation objects for now.
        # We'll actually get the patches when we know which page we're showing.
        all_items = annotations

    num_of_total_results = len(all_items)

    if num_of_total_results == 0:
        # No image results in this search
        errors.append("No image results.")


    # If we're in one of the paginated views, find out what the
    # results on this page are.

    page_results = None
    prev_page_link = None
    next_page_link = None

    if page_view == 'images' or page_view == 'patches':

        paginator = Paginator(all_items, ITEMS_PER_PAGE)

        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            page_results = paginator.page(page)
        except (EmptyPage, InvalidPage):
            page_results = paginator.page(paginator.num_pages)

        # If there are previous or next pages, construct links to them.
        # These links include GET parameters in the form of
        # ?param1=value1&param2=value2 etc.

        if page_results.has_previous():
            prev_page_query_args = request.GET.copy()
            prev_page_query_args.update(dict(page=page_results.previous_page_number()))
            prev_page_link = '?' + urllib.urlencode(prev_page_query_args)
        if page_results.has_next():
            next_page_query_args = request.GET.copy()
            next_page_query_args.update(dict(page=page_results.next_page_number()))
            next_page_link = '?' + urllib.urlencode(next_page_query_args)

        # Finalize the data-structure that holds this page's results.

        if page_view == 'patches':

            # Get an image-patch for each result on the page.
            # Earlier we placeholdered the image patches with the annotation objects,
            # so we're iterating over those annotations now.
            for index, annotation in enumerate(page_results.object_list):

                # TODO: don't hardcode the patch path
                # (this might also apply to the label_main view)
                patchPath = "data/annotations/" + str(annotation.id) + ".jpg"

                page_results.object_list[index] = dict(
                    fullImage=annotation.image,
                    patchPath=patchPath,
                    row=annotation.point.row,
                    col=annotation.point.column,
                    pointNum=annotation.point.point_number,
                )

                generate_patch_if_doesnt_exist(patchPath, annotation)

        else:  # 'images'

            for index, image_obj in enumerate(page_results.object_list):

                page_results.object_list[index] = dict(
                    image_obj=image_obj,
                )


    # If we're showing the metadata form (grid of fields), then prepare that.

    if page_view == 'metadata':

        # Get image statuses (needs annotation, etc.)

        statuses = []
        for image in all_items:
            statuses.append(image.get_annotation_status_str)

        # Initialize the form set with the existing metadata values.

        initValues = {
            'form-TOTAL_FORMS': '%s' % len(all_items),
            'form-INITIAL_FORMS': '%s' % len(all_items),
        }
        initValuesMetadata = initValues

        for i, image in enumerate(all_items):

            # Location keys
            keys = image.get_location_value_str_list()
            for j, key in enumerate(keys):
                initValuesMetadata['form-%s-key%s' % (i,j+1)] = key

            # Image id
            initValuesMetadata['form-%s-image_id' % i] = image.id

            # Other fields
            metadata_field_names = ['photo_date', 'height_in_cm', 'latitude',
                                    'longitude', 'depth', 'camera',
                                    'photographer', 'water_quality',
                                    'strobes', 'framing', 'balance']
            for metadata_field in metadata_field_names:
                formset_field_name = 'form-{num}-{field}'.format(num=i, field=metadata_field)
                initValuesMetadata[formset_field_name] = getattr(image.metadata, metadata_field)

        metadataForm = metadataFormSet(initValuesMetadata)
        checkboxForm = checkboxFormSet(initValues)
        metadataFormWithExtra = zip(metadataForm.forms, checkboxForm.forms, all_items, statuses)
        selectAllCheckbox = CheckboxForm()

    else:

        # Not showing the metadata view.

        metadataForm = None
        metadataFormWithExtra = None
        selectAllCheckbox = None


    # The destination page when you click on an image/patch thumbnail.
    if request.user.has_perm(Source.PermTypes.EDIT.code, source):
        thumbnail_dest_page = 'annotation_tool'
    else:
        thumbnail_dest_page = 'image_detail'


    return render_to_response('visualization/visualize_source.html', {
        'source': source,

        'searchForm': search_form,

        'errors': errors,
        'page_results': page_results,
        'num_of_total_results': num_of_total_results,
        'thumbnail_dest_page': thumbnail_dest_page,
        'prev_page_link': prev_page_link,
        'next_page_link': next_page_link,

        'delete_form': delete_form,
        'download_form': download_form,
        'has_delete_form': bool(delete_form),
        'has_download_form': False,
        # TODO: Uncomment this once downloading is implemented
        #'has_download_form': bool(download_form),

        'key_list': source.get_key_list(),
        'metadataForm': metadataForm,
        'selectAllForm': selectAllCheckbox,
        'metadataFormWithExtra': metadataFormWithExtra,

        'page_view': page_view,
        },
        context_instance=RequestContext(request)
    )


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def metadata_edit_ajax(request, source_id):
    """
    Submitting the metadata-edit form (an Ajax form).
    """
    source = get_object_or_404(Source, id=source_id)

    # This is used to create a formset out of the metadataForm. I need to do this
    # in order to pass in the source id.
    MetadataFormSet = formset_factory(MetadataForm)
    MetadataFormSet.form = staticmethod(curry(MetadataForm, source_id=source_id))

    formset = MetadataFormSet(request.POST)

    if formset.is_valid():

        # Data is valid. Save the data to the database.
        for formData in formset.cleaned_data:

            try:
                image = Image.objects.get(pk=formData['image_id'], source=source)
            except Image.DoesNotExist:
                # If the image doesn't exist in the source (because another
                # source editor deleted the image / someone tampered with the
                # form data / etc.), then just don't do anything for this
                # form instance. Move on to the next one.
                continue

            # Everything except location keys
            metadata_field_names = ['photo_date', 'height_in_cm', 'latitude',
                                    'longitude', 'depth', 'camera',
                                    'photographer', 'water_quality',
                                    'strobes', 'framing', 'balance']

            for metadata_field in metadata_field_names:
                setattr(image.metadata, metadata_field, formData[metadata_field])

            # Location keys
            if 'key1' in formData:
                image.metadata.value1 = formData['key1']
            if 'key2' in formData:
                image.metadata.value2 = formData['key2']
            if 'key3' in formData:
                image.metadata.value3 = formData['key3']
            if 'key4' in formData:
                image.metadata.value4 = formData['key4']
            if 'key5' in formData:
                image.metadata.value5 = formData['key5']

            image.metadata.save()

        # After entering data, try to remove unused key values
        source.remove_unused_key_values()

        return JsonResponse(dict(
            status='success',
        ))

    else:

        error_list = []

        for form in formset:

            for field_name, error_messages in form.errors.iteritems():

                # The form prefix looks something like form-2. The id of the
                # form field element is expected to look like id_form-2-date.
                field_id = 'id_' + form.prefix + '-' + field_name

                # Get the human-readable name for this field.
                field_label = form[field_name].label

                # Get the image this field corresponds to, then get the
                # name (usually is the filename) of that image.
                image_id = form.data[form.prefix + '-image_id']
                img = Image.objects.get(pk=image_id)
                image_name = img.metadata.name
                if image_name == '':
                    image_name = "(Unnamed image)"

                for raw_error_message in error_messages:

                    error_message = '{image_name} | {field_label} | {raw_error_message}'.format(
                        image_name=image_name,
                        field_label=field_label,
                        raw_error_message=raw_error_message,
                    )

                    error_list.append(dict(
                        fieldId=field_id,
                        errorMessage=error_message,
                    ))

        # There were form errors. Return the errors so they can be
        # added to the on-page form via Javascript.
        return JsonResponse(dict(
            status='error',
            errors=error_list,
        ))


@source_permission_required('source_id', perm=Source.PermTypes.EDIT.code)
def browse_delete(request, source_id):
    """
    From the browse images page, select delete as the batch action.
    """
    source = get_object_or_404(Source, id=source_id)

    if request.POST:

        # Get the images from the POST form.
        # Will either be in the form of a list of image ids, or in the form
        # of search args.
        #
        # TODO: if search args, it should also come with the number of
        # images, so that we can do a sanity check (do the number of images
        # match?)

        delete_form = ImageBatchDeleteForm(request.POST, source=source)

        if delete_form.is_valid():
            images_to_delete = delete_form.get_images()

            num_of_images = images_to_delete.count()

            for img in images_to_delete:
                img.delete()

            # try to remove unused key values, after the files are deleted
            source.remove_unused_key_values()

            messages.success(request, 'The {num} selected images have been deleted.'.format(num=num_of_images))

        else:

            messages.success(request, 'The delete form had an error. Nothing was deleted.')

    else:

        messages.success(request, 'The delete form had an error. Nothing was deleted.')

    # Redirect to the default search. Don't try and retrieve the search args
    # that were used previously, because those search args might include
    # location values that don't exist anymore.
    return HttpResponseRedirect(reverse('visualize_source', args=[source_id]))


@source_permission_required('source_id', perm=Source.PermTypes.VIEW.code)
def browse_download(request, source_id):
    """
    From the browse images page, select download as the batch action.
    """
    source = get_object_or_404(Source, id=source_id)

    if request.POST:

        # Get the images from the POST form.
        # Will either be in the form of a list of image ids, or in the form
        # of search args.
        # TODO: if search args, it should also come with the number of
        # images, so that we can do a sanity check (do the number of images
        # match?)

        download_form = ImageBatchDownloadForm(request.POST, source=source)


        if download_form.is_valid():

            images_to_download = download_form.get_images()

            # TODO: Instead of putting up a CSV for download, put the
            # requested images in a .zip (with the images'
            # original filenames) and put that up for download.

            # get the response object, this can be used as a stream.
            response = HttpResponse(mimetype='text/csv')
            # force download.
            response['Content-Disposition'] = 'attachment;filename="images.csv"'
            # the csv writer
            writer = csv.writer(response)
            writer.writerow(["Download test"])

            return response

        else:

            # TODO: Include a way to reach the admin from here. This is a
            # dev error, not a user error
            # TODO: Include search args here too, if any.
            response = HttpResponseRedirect(reverse('visualize_source', args=[source_id]))
            messages.success(request, 'The download form had an error.')

    else:

        # TODO: Include search args here too, if any.
        response = HttpResponseRedirect(reverse('visualize_source', args=[source_id]))
        messages.success(request, 'The download form had an error.')

    return response


@source_visibility_required('source_id')
def generate_statistics(request, source_id):
    errors = []
    years = []
    label_table = []
    group_table = []
    #graph = []

    #generate form to select images to compute statistics for
    source = get_object_or_404(Source, id=source_id)

    #get image search filters
    if request.GET:

        #form to select descriptors to sort images
        form = StatisticsSearchForm(source_id, request.GET)

        if form.is_valid():
            labels = form.cleaned_data['labels']
            groups = form.cleaned_data['groups']

            imageArgs = image_search_args_to_queryset_args(form.cleaned_data, source)

            #Check that the specified set of images and/or labels was found
            if not labels and not groups:
                errors.append("Sorry you didn't specify any labels or groups!")

            #if no errors found, get data needed to plot line graph with
            # coverage on the y axis, and year on the x axis
            if not errors:

                images = Image.objects.filter(source=source, **imageArgs).distinct().select_related()
                patchArgs = dict([('image__'+k, imageArgs[k]) for k in imageArgs])

                #get all annotations for the source that contain the label
                if request.GET and request.GET.get('include_robot', ''):
                    all_annotations = Annotation.objects.filter(source=source, **patchArgs)
                else:
                    all_annotations = Annotation.objects.filter(source=source, **patchArgs).exclude(user=get_robot_user())


                #check that we found annotations
                if all_annotations:
                    #holds the data that gets passed to the graphing code
                    data = []

                    #Format computed data for the graph API to use
                    #TODO: pick easily distinguishable colours from
                    # http://search.cpan.org/~rokr/Color-Library-0.021/lib/Color/Library/Dictionary/WWW.pm
                    # and add them to bucket to be picked randomly
                    bucket = ['00FFFF','32CD32','A52A2A','DC143C','9370DB']
                    legends = []

                    #gets the years we have data for from the specified set of images
                    for image in images:
                        date = image.metadata.photo_date
                        if not date is None:
                            if not years.count(date.year):
                               years.append(date.year)
                    years.sort()

                    for label in labels:
                        table_yearly_counts = []
                        graph_yearly_counts = []
                        #get yearly counts that become y values for the label's line
                        for year in years:
                            #get the most recent for each point for every label specified
                            total_year_annotations =  all_annotations.filter(image__metadata__photo_date__year=year)
                            total_year_annotations_count = total_year_annotations.count()
                            label_year_annotations_count = total_year_annotations.filter(label=label).count()

                            #add up # of annotations, divide by total annotations, and times 100 to get % coverage
                            # done the way it is b/c we need to cast either num or denom as float to get float result,
                            # convert to %, round, then truncate by casting to int
                            try:
                                percent_coverage = (float(label_year_annotations_count)/total_year_annotations_count)*100
                            except ZeroDivisionError:
                                percent_coverage = 0
                            table_yearly_counts.append(round(percent_coverage,2))
                            table_yearly_counts.append(label_year_annotations_count)
                            graph_yearly_counts.append(int(percent_coverage))

                        data.append(graph_yearly_counts)

                        #add label name to legends
                        name = Label.objects.get(id=int(label)).name
                        legends.append(str(name))

                        #create table row to display
                        table_row = [name]
                        table_row.extend(table_yearly_counts)
                        label_table.append(table_row)
                        
                    for group in groups:
                        table_yearly_counts = []
                        graph_yearly_counts = []
                        #get yearly counts that become y values for the label's line
                        for year in years:
                            #get the most recent for each point for every label specified
                            total_year_annotations =  all_annotations.filter(image__metadata__photo_date__year=year)
                            total_year_annotations_count = total_year_annotations.count()
                            label_year_annotations_count = total_year_annotations.filter(label__group=group).count()

                            #add up # of annotations, divide by total annotations, and times 100 to get % coverage
                            # done the way it is b/c we need to cast either num or denom as float to get float result,
                            # convert to %, round, then truncate by casting to int
                            try:
                                percent_coverage = (float(label_year_annotations_count)/total_year_annotations_count)*100
                            except ZeroDivisionError:
                                percent_coverage = 0
                            table_yearly_counts.append(round(percent_coverage,2))
                            table_yearly_counts.append(label_year_annotations_count)
                            graph_yearly_counts.append(int(percent_coverage))

                        data.append(graph_yearly_counts)

                        #add label name to legends
                        name = LabelGroup.objects.get(id=int(group)).name
                        legends.append(str(name))

                        #create table row to display
                        table_row = [name]
                        table_row.extend(table_yearly_counts)
                        group_table.append(table_row)
                    """
                    #Create string of colors
                    colors_string = str(bucket[0: (len(labels)+len(groups))]).replace(' ', '').replace('[','').replace(']','').replace('\'', '')

                    #Create string of labels to put on legend
                    legends_string = str(legends).replace('[', '').replace(']','').replace(' ','').replace('\'', '').replace(',', '|')

                    #Get max y value and add 5 to it
                    max_y = max(map(max,data)) + 5

                    #Calculate new data proportional to max_y to scale graph
                    for elem in data:
                        elem[:] = [x*(100/max_y) for x in elem]

                    #Actually generate the graph now
                    graph = GChart('lc', data, encoding='text', chxt='x,y', chco=colors_string, chdl=legends_string)
                    #draw x axis values from lowest to highest year stepping by 1 year
                    graph.axes.range(0,min(years),max(years),1)
                    #draw y axis values from 0 to (max percent coverage + 5) stepping by 5
                    graph.axes.range(1,0,max_y,5)
                    #Define pixel size to draw graph
                    graph.size(400,400)
                    #Adds the title to the graph
                    graph.title('% Coverage over Years')
                    #Set the line thickness for each dataset
                    count = len(data)
                    while count > 0:
                        graph.line(3,0,0)
                        count -= 1
                    """
                else:
                    errors.append("No data found!")

        else:
            errors.append("Your specified search parameters were invalid!")

    else:
        form = StatisticsSearchForm(source_id)
    
    return render_to_response('visualization/statistics.html', {
        'errors': errors,
        'form': form,
        'source': source,
        'years': years,
        'label_table': label_table,
        'group_table': group_table
        },
        context_instance=RequestContext(request)
    )


# helper function to format abundance corrected outputs with 4 decimal points
def myfmt(r):
    return "%.4f" % (r,)


@source_visibility_required('source_id')
def export_abundance(placeholder, source_id):

    ### SETUP    
    # get the response object, this can be used as a stream.
    response = HttpResponse(mimetype='text/csv')
    # force download.
    response['Content-Disposition'] = 'attachment;filename="abundances.csv"'
    # the csv writer
    writer = csv.writer(response)
    source = get_object_or_404(Source, id=source_id)
    labelset = get_object_or_404(LabelSet, source=source)

    funcgroups = LabelGroup.objects.filter().order_by('id')
    nfuncgroups = len(funcgroups)    
    
    all_annotations = Annotation.objects.filter(source=source).select_related() #get all annotations
    images = Image.objects.filter(source=source).select_related() #get all images
    labels = Label.objects.filter(labelset=labelset).order_by('name')
            
    ### GET THE FUNCTIONAL GROUP CONFUSION MATRIX AND MAKE SOME CHECKS.
    # the second output is a dictionary that maps the group_id to a consecutive number that starts at 0.
    try:
        (fullcm, labelIds) = get_current_confusion_matrix(source_id)
        (cm, fdict, funcIds) = collapse_confusion_matrix(fullcm, labelIds)
    except:
        writer.writerow(["Error! Automated annotator is not availible for this source."])
        return response

    # check if there are classes that never occur in the matrix. 
    emptyinds = logical_and(sum(cm, axis=0)==0, sum(cm,axis=1)==0)

    # set the diagonal entry of these classes to 1. This means that nothing will happen to them.
    for funcgroupitt in range(nfuncgroups):
        if(emptyinds[funcgroupitt]):
            cm[funcgroupitt, funcgroupitt] = 1

    # row-normalize
    (cm_normalized, row_sums) = confusion_matrix_normalize(cm)

    # try inverting
    try:
        Q = linalg.inv(cm_normalized.transpose()) # Q matrix from Solow.
    except:
        writer.writerow(["Error! Confusion matrix is singular, abundance correction is not possible."])
        return response
        
    ### Adds table header which looks something as follows:
    #locKey1 locKey2 locKey3 locKey4 date label1 label2 label3 label4 .... labelEnd
    #Note: labe1, label2, etc corresponds to the percent coverage of that label on
    #a per IMAGE basis, not per source
    header = []
    header.extend(source.get_key_list())
    header.append('date_taken')
    header.append('annotation_status')
    header.extend(images[0].get_metadata_fields_for_export()) #these are the same for all images. Use first one..
    for funcgroup in funcgroups:
        header.append(str(funcgroup.name))
    writer.writerow(header)

    ### BEGIN EXPORT
    vecfmt = vectorize(myfmt) # this is a tool that exports the vector to a nice string with three decimal points
    for image in images:
        locKeys = image.get_location_value_str_list_robust()

        image_annotations = all_annotations.filter(image=image)
        image_annotation_count = image_annotations.count()
        if image_annotation_count == 0:
            image_annotation_count = 1.0 #is there is zero annotations, set this to one, to not mess up the normalization below

        coverage = zeros( (nfuncgroups) ) # this stores the coverage for the current image.
        for label_index, label in enumerate(labels):
            label_annotations_count = all_annotations.filter(image=image, label=label).count() # for each type of label
            coverage[fdict[label.group_id]] += label_annotations_count # increment the count of the group of this label using the fdict dictionary
        coverage /= image_annotation_count #normalize by total count
        coverage *= 100 #make into percent

        row = []
        row.extend(locKeys)
        row.append(str(image.metadata.photo_date))
    
        if image.status.annotatedByHuman:
            row.append('verified_by_human')
        elif image.status.annotatedByRobot:
            row.append('not_verified_by_human_(abundance_corrected)')
            coverage = Q.dot(coverage) #this is the abundance correction. Very simple!
        else:
            row.append('not_annotated')
        row.extend(image.get_metadata_values_for_export())
        row.extend(vecfmt(coverage)) #vecfmt converts to a string with 3 decimal points
        writer.writerow(row)
    
    return response

@source_visibility_required('source_id')
def export_statistics(request, source_id):
    # get the response object, this can be used as a stream.
    response = HttpResponse(mimetype='text/csv')
    # force download.
    response['Content-Disposition'] = 'attachment;filename="statistics.csv"'
    # the csv writer
    writer = csv.writer(response)

    source = get_object_or_404(Source, id=source_id)
    images = Image.objects.filter(source=source).select_related()
    if request.GET.get('robot', ''):
        all_annotations = Annotation.objects.filter(source=source).select_related()
    else:
        all_annotations = Annotation.objects.filter(source=source).exclude(user=get_robot_user()).select_related()
    
    labelset = get_object_or_404(LabelSet, source=source)
    labels = Label.objects.filter(labelset=labelset).order_by('name')
    
    #Adds table header which looks something as follows:
    #locKey1 locKey2 locKey3 locKey4 date label1 label2 label3 label4 .... labelEnd
    #Note: labe1, label2, etc corresponds to the percent coverage of that label on
    #a per IMAGE basis, not per source
    header = []
    header.extend(source.get_key_list())
    header.append('date_taken')
    header.append('annotation_status')
    header.extend(images[0].get_metadata_fields_for_export()) #these are the same for all images. Use first one..
    for label in labels:
        header.append(str(label.name))
    writer.writerow(header)

    zeroed_labels_data = [0 for label in labels]
    #Adds data row which looks something as follows:
    #lter1 out10m line1-2 qu1 20100427  10.2 12.1 0 0 13.2
    for image in images:
        locKeys = image.get_location_value_str_list_robust()

        photo_date = str(image.metadata.photo_date)
        image_labels_data = []
        image_labels_data.extend(zeroed_labels_data)
        image_annotations = all_annotations.filter(image=image)
        total_annotations_count = image_annotations.count()

        for label_index, label in enumerate(labels):
            #Testing out this optimization to see if it's any faster
            label_annotations_count = all_annotations.filter(image=image, label=label).count()
            try:
                label_percent_coverage = (float(label_annotations_count)/total_annotations_count)*100
            except ZeroDivisionError:
                label_percent_coverage = 0
            image_labels_data[label_index] = str(label_percent_coverage)

        row = []
        row.extend(locKeys)
        row.append(photo_date)
        if image.status.annotatedByHuman:
            row.append('verified_by_human')
        elif image.status.annotatedByRobot:
            row.append('not_verified_by_human')
        else:
            row.append('not_annotated')
        row.extend(image.get_metadata_values_for_export())
        row.extend(image_labels_data)
        writer.writerow(row)

    return response

@source_visibility_required('source_id')
def export_annotations(request, source_id):
    # get the response object, this can be used as a stream.
    response = HttpResponse(mimetype='text/csv')
    # force download.
    response['Content-Disposition'] = 'attachment;filename="annotations.csv"'
    # the csv writer
    writer = csv.writer(response)

    source = get_object_or_404(Source, id=source_id)
    images = Image.objects.filter(source=source).select_related()
    if request.GET.get('robot', ''):
        all_annotations = Annotation.objects.filter(source=source)
    else:
        all_annotations = Annotation.objects.filter(source=source).exclude(user=get_robot_user())

    #Add table headings: locKey1 locKey2 locKey3 locKey4 photo_date anno_date row col label shortcode fun_group annotator
    header = []
    header.extend(source.get_key_list())
    header.extend(['photo_date','anno_date','annotator', 'row', 'col', 'label','shortcode', 'func_group'])
    writer.writerow(header)

    #Adds the relevant annotation data in a row
    #Example row: lter1 out10m line1-2 qu1 20100427 20110101 130 230 Porit
    for image in images:
        locKeys = image.get_location_value_str_list_robust()
        photo_date = str(image.metadata.photo_date)

        annotations = all_annotations.filter(image=image).order_by('point').select_related()

        for annotation in annotations:
            label_name = str(annotation.label.name)
            annotation_date = str(annotation.annotation_date)
            annotator = str(annotation.user)
            point_row = str(annotation.point.row)
            point_col = str(annotation.point.column)
            short_code = str(annotation.label.code)
            func_group = str(annotation.label.group)


            row = []
            row.extend(locKeys)
            row.append(photo_date)
            row.append(annotation_date)
            row.append(annotator)
            row.append(point_row)
            row.append(point_col)
            row.append(label_name)
            row.append(short_code)
            row.append(func_group)
            writer.writerow(row)

    return response


@source_visibility_required('source_id')
def export_menu(request, source_id):
    source = get_object_or_404(Source, id=source_id)

    return render_to_response('visualization/export_menu.html', {
        'source': source,
        },
        context_instance=RequestContext(request)
    )
