import csv
import json
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.utils import simplejson
from accounts.utils import get_robot_user
from annotations.models import Annotation, Label, LabelSet, LabelGroup
from decorators import source_visibility_required, source_permission_required
from images.models import Source, Image
from visualization.forms import VisualizationSearchForm, StatisticsSearchForm, ImageBatchDeleteForm, ImageSpecifyForm, ImageBatchDownloadForm
from visualization.utils import generate_patch_if_doesnt_exist
from GChartWrapper import *
from upload.forms import MetadataForm, CheckboxForm
from django.forms.formsets import formset_factory
from django.utils.functional import curry

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

# TODO: Move to utils
def image_search_args_to_url_arg_str(searchDict):
    """
    Take: the image search arguments directly from the visualization search form's
    form.cleaned_data.
    Return: the search arguments in URL get-parameter format.  This is used for
    the next/previous page links.
    """
    argsList = []

    for paramName in searchDict:

        # If a model object (probably coming from a ModelChoiceField in the
        # search form), then set the URL arg to be the primary key
        if isinstance(searchDict[paramName], models.Model):
            argsList.append('%s=%s' % (paramName, searchDict[paramName].pk))

        # Don't include the arg if it's None or '', or 'page' or 'view'
        elif searchDict[paramName] and paramName != 'page' and paramName != 'edit_metadata_view':
            argsList.append('%s=%s' % (paramName, searchDict[paramName]))

    return '&'.join(argsList)

@source_visibility_required('source_id')
def visualize_source(request, source_id):
    """
    View for browsing through a source's images.
    """
    ITEMS_PER_PAGE = 20

    errors = []
    source = get_object_or_404(Source, id=source_id)

    urlArgsStr = ''  # GET args in url format - for constructing prev page/next page links
#    label = False
    imageArgs = dict()

    metadataForm = None
    metadataFormWithExtra = None
    selectAllCheckbox = None
#    view = None


    # Defaults:
    # Image results: all images in the source
    # Search form: with default values
    image_results = Image.objects.filter(source=source)
    search_form = VisualizationSearchForm(source_id)

#    if request.GET:

    # Note that request.GET may be empty. In this case, we just got to the
    # Browse page.
    submitted_search_form = VisualizationSearchForm(source_id, request.GET)

    if submitted_search_form.is_valid():

        # Have the search form on the page start with the values
        # submitted in this search.
        search_form = submitted_search_form

        urlArgsStr = image_search_args_to_url_arg_str(search_form.cleaned_data)

        # TODO: Shouldn't need this anymore
        imageArgs = image_search_args_to_queryset_args(search_form.cleaned_data, source)
    else:
        messages.error(request, 'There were errors in the search parameters.')


    label = search_form.cleaned_data['labels']
    edit_metadata_view = search_form.cleaned_data['edit_metadata_view']


    # TODO: Ideally, we'd simply fill in the image specify form with the
    # request.POST (and/or request.GET) and that'll take care of all cases
    # where we can reach this page.
    if request.POST and 'image_specify_form_from_upload' in request.POST:
        # TODO: If coming from the upload page, we expect the upload page to
        # properly fill in an ImageSpecifyForm with the image ids.
        image_specify_form = ImageSpecifyForm(request.POST, source=source)
    else:
        # Use the search form.
        image_specify_form = ImageSpecifyForm(
            dict(
                specify_method='search_keys',
                specify_str=json.dumps(search_form.cleaned_data),
            ),
            source=source,
        )

    # TODO: Is it enough to set these forms as None by default?
    image_batch_delete_form = None
    image_batch_download_form = None

    if image_specify_form.is_valid():
        image_results = image_specify_form.get_images()

        # Give the delete form the same stuff as the image
        # specify form.
        image_batch_delete_form = ImageBatchDeleteForm(
            image_specify_form.data,
            source=source,
        )
        image_batch_download_form = ImageBatchDownloadForm(
            image_specify_form.data,
            source=source,
        )


    # Get the search results (all of them, not just on this page).

    #if user did not specify a label to generate patches for, assume they want to view whole images
    if not label:

        showPatches = False
        all_items = image_results

        # Sort the images.
        # TODO: Stop duplicating this DB-specific extras query; put it in a separate function...
        # Also, despite the fact that we're dealing with images and not metadatas, selecting photo_date does indeed work.
        db_extra_select = {'metadata__year': 'YEAR(photo_date)'}  # YEAR() is MySQL only, PostgreSQL has different syntax

        sort_keys = ['metadata__'+k for k in (['year'] + source.get_value_field_list())]
        all_items = all_items.extra(select=db_extra_select)
        all_items = all_items.order_by(*sort_keys)


        if edit_metadata_view:

            # Show the metadata form (grid of fields).

            # Get images and statuses
            images = [];
            statuses = [];
            for i, image in enumerate(all_items):
                images.append(image)
                statuses.append(image.get_annotation_status_str)

            # This is used to create a formset out of the metadataForm. I need to do this
            # in order to pass in the source id.
            metadataFormSet = formset_factory(MetadataForm)
            metadataFormSet.form = staticmethod(curry(MetadataForm, source_id=source_id))

            # There is a separate form that controls the checkboxes.
            checkboxFormSet = formset_factory(CheckboxForm)

            if request.method == 'POST' and 'metadata_form' in request.POST and request.user.has_perm(Source.PermTypes.EDIT.code, source):
                metadataForm = metadataFormSet(request.POST)
                selectAllCheckbox = CheckboxForm(request.POST)
                checkboxForm = checkboxFormSet(request.POST)
                metadataFormWithExtra = zip(metadataForm.forms, checkboxForm.forms, images, statuses)
                if metadataForm.is_valid():
                    # Here we save the data to the database, since data is valid.
                    for image, formData in zip(all_items, metadataForm.cleaned_data):
                        image.metadata.photo_date = formData['date']
                        image.metadata.height_in_cm = formData['height']
                        image.metadata.latitude = formData['latitude']
                        image.metadata.longitude = formData['longitude']
                        image.metadata.depth = formData['depth']
                        image.metadata.camera = formData['camera']
                        image.metadata.photographer = formData['photographer']
                        image.metadata.water_quality = formData['waterQuality']
                        image.metadata.strobes = formData['strobes']
                        image.metadata.framing = formData['framingGear']
                        image.metadata.balance = formData['whiteBalance']

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
                    messages.success(request, 'Image metadata file has now been saved.')
                else:
                    # Display error message in addition to other error messages below.
                    messages.error(request, 'Please correct the errors below.')
            else:
                # This initializes the form set with default values; namely, the values
                # for the keys that already exist in our records.
                initValues = {'form-TOTAL_FORMS': '%s' % len(all_items), 'form-INITIAL_FORMS': '%s' % len(all_items)}
                initValuesMetadata = initValues
                for i, image in enumerate(all_items):
                    keys = image.get_location_value_str_list()
                    for j, key in enumerate(keys):
                        initValuesMetadata['form-%s-key%s' % (i,j+1)] = key
                    initValuesMetadata['form-%s-date' % i] = image.metadata.photo_date
                    initValuesMetadata['form-%s-height' % i] = image.metadata.height_in_cm
                    initValuesMetadata['form-%s-latitude' % i] = image.metadata.latitude
                    initValuesMetadata['form-%s-longitude' % i] = image.metadata.longitude
                    initValuesMetadata['form-%s-depth' % i] = image.metadata.depth
                    initValuesMetadata['form-%s-camera' % i] = image.metadata.camera
                    initValuesMetadata['form-%s-photographer' % i] = image.metadata.photographer
                    initValuesMetadata['form-%s-waterQuality' % i] = image.metadata.water_quality
                    initValuesMetadata['form-%s-strobes' % i] = image.metadata.strobes
                    initValuesMetadata['form-%s-framingGear' % i] = image.metadata.framing
                    initValuesMetadata['form-%s-whiteBalance' % i] = image.metadata.balance
                metadataForm = metadataFormSet(initValuesMetadata)
                checkboxForm = checkboxFormSet(initValues)
                metadataFormWithExtra = zip(metadataForm.forms, checkboxForm.forms, images, statuses)
                selectAllCheckbox = CheckboxForm()

    else:
        #since user specified a label, generate patches to show instead of whole images
        showPatches = True
        patchArgs = dict([('image__'+k, imageArgs[k]) for k in imageArgs])

        #get all annotations for the source that contain the label
        try:
            annotator = int(submitted_search_form.cleaned_data.pop('annotator'))
        except ValueError:
            annotator = 2
        annotations = Annotation.objects.filter(source=source, label=label, **patchArgs).order_by('?')
        if not annotator:
            annotations.exclude(user=get_robot_user())
        elif annotator == 1:
            annotations.filter(user=get_robot_user())

        # Placeholder the image patches with the annotation objects for now.
        # We'll actually get the patches when we know which page we're showing.
        all_items = annotations

    if not all_items:
        if request.GET:
            # No image results in this search
            errors.append("Sorry, no images matched your query")
        else:
            # No image results, and just got to the visualization page
            errors.append("Sorry, there are no images for this source yet. Please upload some.")

    paginator = Paginator(all_items, ITEMS_PER_PAGE)

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

            # TODO: don't hardcode the patch path
            # (this might also apply to the label_main view)
            patchPath = "data/annotations/" + str(annotation.id) + ".jpg"

            images.object_list[index] = dict(
                type="patches",
                fullImage=annotation.image,
                patchPath=patchPath,
                row=annotation.point.row,
                col=annotation.point.column,
                pointNum=annotation.point.point_number,
            )

            generate_patch_if_doesnt_exist(patchPath, annotation)

    else:

        for index, image_obj in enumerate(images.object_list):

            images.object_list[index] = dict(
                type="full_images",
                image_obj=image_obj,
            )

    return render_to_response('visualization/visualize_source.html', {
        'errors': errors,
        'searchForm': search_form,
        'source': source,
        'images': images,
        'showPatches': showPatches,
        'searchParamsStr': urlArgsStr,
#        'actionForm': actionForm,
        'image_batch_delete_form': image_batch_delete_form,
        'image_batch_download_form': image_batch_download_form,
        'key_list': source.get_key_list(),
        'metadataForm': metadataForm,
        'selectAllForm': selectAllCheckbox,
        'metadataFormWithExtra': metadataFormWithExtra,
        'view': edit_metadata_view,
        },
        context_instance=RequestContext(request)
    )


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
        # TODO: if search args, it should also come with the number of
        # images, so that we can do a sanity check (do the number of images
        # match?)

        delete_form = ImageBatchDeleteForm(request.POST, source=source)

        if delete_form.is_valid():
            images_to_delete = delete_form.get_images()

    #        actionFormImageArgs = simplejson.loads(searchKeys)
    #        imagesToDelete = Image.objects.filter(source=source, **actionFormImageArgs)

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

    # TODO: Include search args here too, if any.
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
    for label in labels:
        header.append(str(label.name))
    writer.writerow(header)

    zeroed_labels_data = [0 for label in labels]
    #Adds data row which looks something as follows:
    #lter1 out10m line1-2 qu1 20100427  10.2 12.1 0 0 13.2
    for image in images:
        locKeys = []
        for field in image.get_location_value_str_list():
            if field:
                locKeys.append(str(field))
            else:
                locKeys.append("Unspecified")

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
        locKeys = []
        for field in image.get_location_value_str_list():
            if field:
                locKeys.append(str(field))
            else:
                locKeys.append("Unspecified")
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