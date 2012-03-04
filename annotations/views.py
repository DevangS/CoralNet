from collections import OrderedDict
from datetime import datetime
from operator import itemgetter
import pickle
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils import simplejson
import reversion
from accounts.utils import get_robot_user
from annotations.forms import NewLabelForm, NewLabelSetForm, AnnotationForm
from annotations.models import Label, LabelSet, Annotation, AnnotationToolAccess
from CoralNet.decorators import labelset_required, permission_required, visibility_required
from annotations.utils import get_old_annotation_user_display
from images.model_utils import AnnotationAreaUtils
from images.models import Source, Image, Point
from visualization.utils import generate_patch_if_doesnt_exist

@login_required
def label_new(request):
    """
    Page to create a new label for CoralNet.
    NOTE: This view might be obsolete, deferring in favor of
    having the new-label form only be in the create-labelset page.
    """
    if request.method == 'POST':
        form = NewLabelForm(request.POST)

        if form.is_valid():
            label = form.save()
            messages.success(request, 'Label successfully created.')
            return HttpResponseRedirect(reverse('label_main', args=[label.id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NewLabelForm()

    return render_to_response('annotations/label_new.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
    )

@permission_required(Source.PermTypes.ADMIN.code, (Source, 'id', 'source_id'))
def labelset_new(request, source_id):
    """
    Page to create a labelset for a source.
    """

    source = get_object_or_404(Source, id=source_id)
    showLabelForm = False
    initiallyCheckedLabels = []

    if request.method == 'POST':

        initiallyCheckedLabels = [int(labelId) for labelId in request.POST.getlist('labels')]

        if 'create_label' in request.POST:
            labelForm = NewLabelForm(request.POST, request.FILES)
            newLabel = None

            # is_valid() checks for label conflicts in the database (same-name label found, etc.).
            if labelForm.is_valid():
                newLabel = labelForm.instance
                newLabel.created_by = request.user
                newLabel.save()
                messages.success(request, 'Label successfully created.')
            else:
                messages.error(request, 'Please correct the errors below.')
                showLabelForm = True

            # The labelset form should now have the new label.
            labelSetForm = NewLabelSetForm()

            # If a label was added, the user probably wanted to add it to their
            # labelset, so pre-check that label.
            if newLabel:
                initiallyCheckedLabels.append(newLabel.id)

        else:  # 'create_labelset' in request.POST
            labelSetForm = NewLabelSetForm(request.POST)
            labelForm = NewLabelForm()

            if labelSetForm.is_valid():
                labelset = labelSetForm.save()
                source.labelset = labelset
                source.save()

                messages.success(request, 'LabelSet successfully created.')
                return HttpResponseRedirect(reverse('labelset_main', args=[source.id]))
            else:
                messages.error(request, 'Please correct the errors below.')
    
    else:
        labelForm = NewLabelForm()
        labelSetForm = NewLabelSetForm()

    allLabels = [dict(labelId=str(id), name=label.name,
                      code=label.code, group=label.group.name)
                 for id, label in labelSetForm['labels'].field.choices]

    # Dict that tells whether a label should be initially checked: {85: True, 86: True, ...}.
    isInitiallyChecked = dict()
    for labelId, label in labelSetForm['labels'].field.choices:
        isInitiallyChecked[labelId] = labelId in initiallyCheckedLabels
        
    return render_to_response('annotations/labelset_new.html', {
        'showLabelFormInitially': simplejson.dumps(showLabelForm),    # Convert Python bool to JSON bool
        'labelSetForm': labelSetForm,
        'labelForm': labelForm,
        'source': source,
        'isEditLabelsetForm': False,

        'allLabels': allLabels,    # label dictionary, for accessing as a template variable
        'allLabelsJSON': simplejson.dumps(allLabels),    # label dictionary, for JS
        'isInitiallyChecked': simplejson.dumps(isInitiallyChecked),
        },
        context_instance=RequestContext(request)
    )

@permission_required(Source.PermTypes.ADMIN.code, (Source, 'id', 'source_id'))
def labelset_edit(request, source_id):
    """
    Page to edit a source's labelset.
    """

    source = get_object_or_404(Source, id=source_id)
    labelset = source.labelset

    if labelset.isEmptyLabelset():
        return HttpResponseRedirect(reverse('labelset_new', args=[source.id]))

    showLabelForm = False
    labelsInLabelset = [label.id for label in labelset.labels.all()]
    initiallyCheckedLabels = labelsInLabelset

    if request.method == 'POST':

        initiallyCheckedLabels = [int(labelId) for labelId in request.POST.getlist('labels')]

        if 'create_label' in request.POST:
            labelForm = NewLabelForm(request.POST, request.FILES)
            newLabel = None

            # is_valid() checks for label conflicts in the database (same-name label found, etc.).
            if labelForm.is_valid():
                newLabel = labelForm.instance
                newLabel.created_by = request.user
                newLabel.save()
                messages.success(request, 'Label successfully created.')
            else:
                messages.error(request, 'Please correct the errors below.')
                showLabelForm = True

            # The labelset form should now have the new label.
            labelSetForm = NewLabelSetForm()

            # If a label was added, the user probably wanted to add it to their
            # labelset, so pre-check that label.
            if newLabel:
                initiallyCheckedLabels.append(newLabel.id)

        elif 'edit_labelset' in request.POST:
            labelSetForm = NewLabelSetForm(request.POST, instance=labelset)
            labelForm = NewLabelForm()

            if labelSetForm.is_valid():
                labelSetForm.save()

                messages.success(request, 'LabelSet successfully edited.')
                return HttpResponseRedirect(reverse('labelset_main', args=[source.id]))
            else:
                messages.error(request, 'Please correct the errors below.')

        else: # Cancel
            messages.success(request, 'Edit cancelled.')
            return HttpResponseRedirect(reverse('labelset_main', args=[source_id]))

    else:
        labelForm = NewLabelForm()
        labelSetForm = NewLabelSetForm(instance=labelset)

    # Dictionary of info for each label in the labelset form.
    allLabels = [dict(labelId=str(id), name=label.name,
                      code=label.code, group=label.group.name)
                 for id, label in labelSetForm['labels'].field.choices]

    # Dict that tells whether a label is already in the labelset: {85: True, 86: True, ...}.
    # This is basically a workaround around JavaScript's lack of a widely supported "is element in list" function.
    isInLabelset = dict()
    for labelId, label in labelSetForm['labels'].field.choices:
        isInLabelset[labelId] = labelId in labelsInLabelset

    # Dict that tells whether a label should be initially checked: {85: True, 86: True, ...}.
    isInitiallyChecked = dict()
    for labelId, label in labelSetForm['labels'].field.choices:
        isInitiallyChecked[labelId] = labelId in initiallyCheckedLabels

    # Dict that tells whether an initially-checked label's status is changeable: {85: True, 86: False, ...}.
    # A label is unchangeable if it's being used by any annotations in this source.
    isLabelUnchangeable = dict()
    for labelId, label in labelSetForm['labels'].field.choices:
        if labelId in initiallyCheckedLabels:
            annotationsForLabel = Annotation.objects.filter(image__source=source, label__id=labelId)
            isLabelUnchangeable[labelId] = len(annotationsForLabel) > 0
        else:
            isLabelUnchangeable[labelId] = False


    return render_to_response('annotations/labelset_edit.html', {
        'showLabelFormInitially': simplejson.dumps(showLabelForm),    # Python bool to JSON bool
        'labelSetForm': labelSetForm,
        'labelForm': labelForm,
        'source': source,
        'isEditLabelsetForm': True,

        'allLabels': allLabels,    # label dictionary, for accessing as a template variable
        'allLabelsJSON': simplejson.dumps(allLabels),    # label dictionary, for JS
        'isInLabelset': simplejson.dumps(isInLabelset),
        'isInitiallyChecked': simplejson.dumps(isInitiallyChecked),
        'isLabelUnchangeable': simplejson.dumps(isLabelUnchangeable),
        },
        context_instance=RequestContext(request)
    )

def label_main(request, label_id):
    """
    Main page for a particular label
    """

    label = get_object_or_404(Label, id=label_id)

    sources_with_label = Source.objects.filter(labelset__labels=label).order_by('name')
    visible_sources_with_label = [s for s in sources_with_label if s.visible_to_user(request.user)]

    # Differentiate between the sources that the user is part of
    # and the other public sources.  Sort the source list accordingly, too.
    sources_of_user = Source.get_sources_of_user(request.user)

    source_types = []
    for s in visible_sources_with_label:
        if s in sources_of_user:
            source_types.append('mine')
        else:
            source_types.append('public')

    visible_sources_with_label = zip(source_types, visible_sources_with_label)
    visible_sources_with_label.sort(key=lambda x: x[0])  # Mine first, then public

    # Example patches.
    # TODO: don't hardcode the patch path
    example_annotations = Annotation.objects.filter(label=label, image__source__visibility=Source.VisibilityTypes.PUBLIC).exclude(user=get_robot_user()).order_by('?')[:5]
    patches = [dict(
                  annotation=a,
                  fullImage=a.image,
                  source=a.image.source,
                  patchPath="data/annotations/" + str(a.id) + ".jpg",
                  row=a.point.row,
                  col=a.point.column,
                  pointNum=a.point.point_number,
              )
              for a in example_annotations]

    for p in patches:
        generate_patch_if_doesnt_exist(p['patchPath'], p['annotation'])


    return render_to_response('annotations/label_main.html', {
        'label': label,
        'visible_sources_with_label': visible_sources_with_label,
        'patches': patches,
        },
        context_instance=RequestContext(request)
    )


@visibility_required('source_id')
def labelset_main(request, source_id):
    """
    Main page for a particular source's labelset
    """

    source = get_object_or_404(Source, id=source_id)

    labelset = source.labelset
    if labelset.isEmptyLabelset():
        return HttpResponseRedirect(reverse('labelset_new', args=[source.id]))

    labels = labelset.labels.all().order_by('group__id', 'name')


    return render_to_response('annotations/labelset_main.html', {
            'source': source,
            'labelset': labelset,
            'labels': labels,
            },
            context_instance=RequestContext(request)
    )

def labelset_list(request):
    """
    Page with a list of all the labelsets

    Not sure where to put a link to this page. It's a little less
    useful when each source has its own labelset, but this view still
    might be useful if someone wants to browse through labelsets that
    they could base their labelset off of.
    """

    publicSources = Source.objects.filter(visibility=Source.VisibilityTypes.PUBLIC)
    publicSourcesWithLabelsets = publicSources.exclude(labelset=LabelSet.getEmptyLabelset())

    return render_to_response('annotations/labelset_list.html', {
                'publicSourcesWithLabelsets': publicSourcesWithLabelsets,
                },
                context_instance=RequestContext(request)
    )

def label_list(request):
    """
    Page with a list of all the labels
    """

    labels = Label.objects.all().order_by('group__id', 'name')

    return render_to_response('annotations/label_list.html', {
                'labels': labels,
                },
                context_instance=RequestContext(request)
    )


@permission_required(Source.PermTypes.EDIT.code, (Source, 'id', 'source_id'))
@labelset_required('source_id', 'You need to create a labelset for your source before you can annotate images.')
def annotation_tool(request, image_id, source_id):
    """
    View for the annotation tool.
    """

    image = get_object_or_404(Image, id=image_id)
    source = get_object_or_404(Source, id=source_id)
    metadata = image.metadata
    annotation_area_string = AnnotationAreaUtils.annotation_area_string_of_img(image)

    # Get all labels, ordered first by functional group, then by short code.
    labels = source.labelset.labels.all().order_by('group', 'code')
    # Get labels in the form {'code': <short code>, 'group': <functional group>}.
    # Convert from a ValuesQuerySet to a list to make the structure JSON-serializable.
    labelValues = list(labels.values('code', 'group'))

    form = AnnotationForm(image=image, user=request.user)

    pointValues = Point.objects.filter(image=image).values(
        'point_number', 'row', 'column')
    annotationValues = Annotation.objects.filter(image=image).values(
        'point__point_number', 'label__name', 'label__code')

    # annotationsDict
    # keys: point numbers
    # values: dicts containing the values in pointValues and
    #         annotationValues (if the point has an annotation) above
    annotationsDict = dict()
    for p in pointValues:
        annotationsDict[p['point_number']] = p
    for a in annotationValues:
        annotationsDict[a['point__point_number']].update(a)

    # Get a list of the annotationsDict values (the keys are discarded)
    # Sort by point_number
    annotations = list(annotationsDict.values())
    annotations.sort(key=lambda x:x['point_number'])

    # Now we've gotten all the relevant points and annotations
    # from the database, in a list of dicts:
    # [{'point_number':1, 'row':294, 'column':749, 'label__name':'Porites', 'label__code':'Porit', 'user_is_robot':False},
    #  {'point_number':2, ...},
    #  ...]
    # TODO: Are we even using anything besides row, column, and point_number?  If not, discard the annotation fields to avoid confusion.

    access = AnnotationToolAccess(image=image, source=source, user=request.user)
    access.save()

    return render_to_response('annotations/annotation_tool.html', {
        'source': source,
        'image': image,
        'metadata': metadata,
        'annotation_area_string': annotation_area_string,
        'labels': labelValues,
        'labelsJSON': simplejson.dumps(labelValues),
        'form': form,
        'location_values': ', '.join(image.get_location_value_str_list()),
        'annotations': annotations,
        'annotationsJSON': simplejson.dumps(annotations),
        'num_of_points': len(annotations),
        'num_of_annotations': len(annotationValues),
        },
        context_instance=RequestContext(request)
    )


@permission_required(Source.PermTypes.EDIT.code, (Source, 'id', 'source_id'))
def annotation_history(request, image_id, source_id):
    """
    View for an image's annotation history.
    """

    image = get_object_or_404(Image, id=image_id)
    source = get_object_or_404(Source, id=source_id)

    annotations = Annotation.objects.filter(image=image, source=source).order_by('point__point_number')

#    anno_versions_by_anno_obj = [reversion.get_for_object(anno) for anno in annotations]

    anno_versions_flat_list = []
#    for sublist in anno_versions_by_anno_obj:
#        for anno_version in sublist:
    for anno in annotations:
        point_number = anno.point.point_number

        for anno_version in reversion.get_for_object(anno):
            label_id = anno_version.field_dict['label']
            label_code = Label.objects.get(pk=label_id).code

            event_str = "Point %s: %s" % (
                point_number,
                label_code,
                )
            # TODO: Use datetime and user from the serialized data, or from the revision's fields?
            # Problem with the revision's fields is that the initial revisions have a blank user.  In this case the initial revision's data is useless, but the initial revision's serialized data isn't.  Also, the revision's fields obviously don't have the robot version.
            # Problem with the serialized data is, well... getting the datetime back depends on how it's serialized.
            anno_versions_flat_list.append(
                dict(
                    event_str=event_str,
                    type='annotation',
                    date=anno_version.field_dict['annotation_date'],
                    user=get_old_annotation_user_display(anno_version),
                )
            )

    anno_tool_accesses = []
    for access in AnnotationToolAccess.objects.filter(image=image, source=source):

        event_str = "Accessed annotation tool"
        anno_tool_accesses.append(
            dict(
                event_str=event_str,
                type='access',
                date=access.access_date,
                user=access.user.username,
            )
        )

    anno_events_unsorted = anno_versions_flat_list + anno_tool_accesses

    # Ultimate goal is to get a list of:
    # dict(
    #   date = somedate
    #   user = someuser
    #   events = [event1, event2, ...]
    # )

    # TODO: Accommodate the robot version field to differentiate between
    # different robot versions.

    # TODO: Just use tuples as the keys.  No need to pickle things.
    # See http://stackoverflow.com/questions/4878881/python-tuples-dictionaries-as-keys-select-sort
    event_dict = dict()
    for event in anno_events_unsorted:
#        key = pickle.dumps(
#            (event['date'], event['user'])
#        )
        key = (event['date'], event['user'])
        if event_dict.has_key(key):
            event_dict[key].append(event['event_str'])
        else:
            event_dict[key] = [event['event_str']]

    #tuple_keys = [pickle.loads(k) for k in event_dict.keys()]
    keys = event_dict.keys()

    # Sort from latest to earliest date.
    # Within the same date, sort by user.
    keys.sort(key=itemgetter(1))    # Sort by user
    keys.sort(key=itemgetter(0), reverse=True)    # Now sort by date, descending

    event_list_sorted = []
    for key in keys:
        #pickled_key = pickle.dumps(key)
        event_list_sorted.append(
            dict(
                date=key[0],
                user=key[1],
                events=event_dict[key],
            )
        )

    return render_to_response('annotations/annotation_history.html', {
        'source': source,
        'image': image,
        'anno_log': event_list_sorted,
        },
        context_instance=RequestContext(request)
    )