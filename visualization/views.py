import csv
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import transaction, models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.utils import simplejson
from accounts.utils import get_robot_user
from annotations.models import Annotation, Label, LabelSet
from CoralNet.decorators import visibility_required
from images.models import Source, Image
from visualization.forms import VisualizationSearchForm, ImageBatchActionForm, StatisticsSearchForm
from visualization.utils import generate_patch_if_doesnt_exist
from GChartWrapper import *

def image_search_args_to_queryset_args(searchDict):
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

        # Don't include the arg if it's None or '', or 'page'
        elif searchDict[paramName] and paramName != 'page':
            argsList.append('%s=%s' % (paramName, searchDict[paramName]))

    return '&'.join(argsList)


@transaction.commit_on_success
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

            label = form.cleaned_data.pop('labels')
            imageArgs = image_search_args_to_queryset_args(form.cleaned_data)

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
                    img.delete()

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
        #if user did not specify a label to generate patches for, assume they want to view whole images
        if not label:
            showPatches = False
            allSearchResults = Image.objects.filter(source=source, **imageArgs).order_by('-upload_date')

        else:
            #since user specified a label, generate patches to show instead of whole images
            showPatches = True
            patchArgs = dict([('image__'+k, imageArgs[k]) for k in imageArgs])

            #get all annotations for the source that contain the label
            annotations = Annotation.objects.filter(source=source, label=label, **patchArgs).exclude(user=get_robot_user())

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

@visibility_required('source_id')
def generate_statistics(request, source_id):
    errors = []

    #default graph to show, gets overwritten later if sanity checks passed
    graph = Line([0]).title('Specify some data to view the statistics')

    #generate form to select images to compute statistics for
    source = get_object_or_404(Source, id=source_id)

    #get image search filters
    if request.GET:

        #form to select descriptors to sort images
        form = StatisticsSearchForm(source_id, request.GET)

        if form.is_valid():
            labels = form.cleaned_data['labels']
            imageArgs = image_search_args_to_queryset_args(form.cleaned_data)

            #Check that the specified set of images and/or labels was found
            if not labels:
                errors.append("Sorry you didn't specify any labels!")

            #if no errors found, get data needed to plot line graph with
            # coverage on the y axis, and year on the x axis
            if not errors:

                images = Image.objects.filter(source=source, **imageArgs).order_by('-upload_date').select_related()
                patchArgs = dict([('image__'+k, imageArgs[k]) for k in imageArgs])

                #get all non-robot annotations for the source
                all_annotations = Annotation.objects.filter(source=source, **patchArgs).exclude(user=get_robot_user())

                #holds the data that gets passed to the graphing code
                data = [] #TODO: figure out why data isn't being generated correctly
                years = []

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
                    yearly_counts = []

                    #get yearly counts that become y values for the label's line
                    for year in years:
                        #get the most recent for each point for every label specified
                        total_year_annotations =  all_annotations.filter(image__metadata__photo_date__year=year).distinct()
                        label_year_annotations = [annotation for annotation in total_year_annotations if annotation.label == label]

                        #add up # of annotations, divide by total annotations, and times 100 to get % coverage
                        # done the way it is b/c we need to cast either num or denom as float to get float result,
                        # convert to %, round, then truncate by casting to int
                        try:
                            percent_coverage = int(round((float(len(label_year_annotations))/len(total_year_annotations))*100))
                        except ZeroDivisionError:
                            percent_coverage = 0
                        yearly_counts.append(percent_coverage)

                    data.append(yearly_counts)
                    #add label name to legends
                    label_id = int(label)
                    label_temp = Label.objects.get(id=label_id)
                    name = label_temp.name
                    legends.append(str(name)) #TODO: really need to optimize

                #Create string of colors
                colors_string = str(bucket[0:len(labels)]).replace(' ', '').replace('[','').replace(']','').replace('\'', '')

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
                    
        else:
            errors.append("Your specified search parameters were invalid!")

    else:
        form = StatisticsSearchForm(source_id)
    
    return render_to_response('visualization/statistics.html', {
        'errors': errors,
        'form': form,
        'source': source,
        'graph': graph
        },
        context_instance=RequestContext(request)
    )

@visibility_required('source_id')
def export_statistics(request, source_id):
    # get the response object, this can be used as a stream.
    response = HttpResponse(mimetype='text/csv')
    # force download.
    response['Content-Disposition'] = 'attachment;filename="statistics.csv"'
    # the csv writer
    writer = csv.writer(response)

    source = get_object_or_404(Source, id=source_id)
    images = Image.objects.filter(source=source).select_related()
    all_annotations = Annotation.objects.filter(source=source).exclude(user=get_robot_user()).select_related()
    labels = get_object_or_404(LabelSet, source=source).labels

    #Adds table header which looks something as follows:
    #locKey1 locKey2 locKey3 locKey4 date label1 label2 label3 label4 .... labelEnd
    #Note: labe1, label2, etc corresponds to the percent coverage of that label on
    #a per IMAGE basis, not per source
    header = []
    header.extend(source.get_key_list())
    header.append('date')
    writer.writerow(header)

    zeroed_labels_data = [0 for label in labels]
    #Adds data row which looks something as follows:
    #lter1 out10m line1-2 qu1 20100427  10.2 12.1 0 0 13.2
    for image in images:
        locKeys = [str(i) for i in image.get_location_value_str_list()]
        photo_date = str(image.metadata.photo_date)
        image_labels_data = []
        image_labels_data.extend(zeroed_labels_data)
        image_annotations = [annotation for annotation in all_annotations if annotation.image == image]
        total_annotations_count = len(image_annotations)

        for label_index, label in enumerate(labels):
            label_percent_coverage = (image_annotations.filter(label=label).count()/total_annotations_count)*100
            image_labels_data[label_index] = str(label_percent_coverage)

        row = []
        row.extend(locKeys)
        row.append(photo_date)
        row.extend(image_labels_data)
        writer.writerow(row)

    return response

@visibility_required('source_id')
def export_annotations(request, source_id):
    # get the response object, this can be used as a stream.
    response = HttpResponse(mimetype='text/csv')
    # force download.
    response['Content-Disposition'] = 'attachment;filename="annotations.csv"'
    # the csv writer
    writer = csv.writer(response)

    source = get_object_or_404(Source, id=source_id)
    images = list(Image.objects.filter(source=source))
    all_annotations = list(Annotation.objects.filter(source=source))

    #Add table headings: locKey1 locKey2 locKey3 locKey4 photo_date anno_date row col label
    header = []
    header.extend(source.get_key_list())
    header.extend(['photo_date','anno_date', 'row', 'col', 'label'])
    writer.writerow(header)

    #Adds the relevant annotation data in a row
    #Example row: lter1 out10m line1-2 qu1 20100427 20110101 130 230 Porit
    for image in images:
        locKeys =  [str(i) for i in image.get_location_value_str_list()]
        photo_date = str(image.metadata.photo_date)

        annotations = all_annotations.filter(image=image).order_by('point').select_related()

        for annotation in annotations:
            label_name = str(annotation.label.name)
            annotation_date = str(annotation.annotation_date)
            point_row = str(annotation.point.row)
            point_col = str(annotation.point.column)

            row = []
            row.extend(locKeys)
            row.append(photo_date)
            row.append(annotation_date)
            row.append(point_row)
            row.append(point_col)
            row.append(label_name)
            
            writer.writerow(row)

    return response


def export_menu(request, source_id):
    source = get_object_or_404(Source, id=source_id)

    return render_to_response('visualization/export_menu.html', {
        'source': source,
        },
        context_instance=RequestContext(request)
    )