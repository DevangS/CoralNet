from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils import simplejson
from annotations.forms import NewLabelForm, NewLabelSetForm, AnnotationForm
from annotations.models import Label, LabelSet, Annotation
from CoralNet.decorators import labelset_required, permission_required, visibility_required
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
    example_annotations = Annotation.objects.filter(label=label, image__source__visibility=Source.VisibilityTypes.PUBLIC).order_by('?')[:5]
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


@labelset_required('source_id', 'You need to create a labelset for your source before you can annotate images.')
@permission_required(Source.PermTypes.EDIT.code, (Source, 'id', 'source_id'))
def annotation_tool(request, image_id, source_id):
    """
    View for the annotation tool.
    """

    image = get_object_or_404(Image, id=image_id)
    source = get_object_or_404(Source, id=source_id)
    metadata = image.metadata
    labelCodes = [d['code'] for d in source.labelset.labels.all().values('code')]

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

    return render_to_response('annotations/annotation_tool.html', {
        'source': source,
        'image': image,
        'metadata': metadata,
        'labelCodes': labelCodes,
        'labelCodesJSON': simplejson.dumps(labelCodes),
        'form': form,
        'location_values': ', '.join(image.get_location_value_str_list()),
        'annotations': annotations,
        'annotationsJSON': simplejson.dumps(annotations),
        'num_of_points': len(annotations),
        'num_of_annotations': len(annotationValues),
        },
        context_instance=RequestContext(request)
    )