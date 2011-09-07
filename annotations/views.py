from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from guardian.decorators import permission_required
from annotations.forms import NewLabelForm, NewLabelSetForm
from annotations.models import Label, LabelSet, Annotation
from images.models import Source, Image, Point

@login_required
def label_new(request):
    """
    Page to create a new label for CoralNet.
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

@login_required
def labelset_new(request, source_id):
    """
    Page to create a labelset for a source.
    """

    source = get_object_or_404(Source, id=source_id)

    if request.method == 'POST':
        form = NewLabelSetForm(request.POST)

        if form.is_valid():
            labelset = form.save()
            source.labelset = labelset
            source.save()

            messages.success(request, 'LabelSet successfully created.')
            return HttpResponseRedirect(reverse('labelset_main', args=[source.id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NewLabelSetForm()

    return render_to_response('annotations/labelset_new.html', {
        'form': form,
        'source': source,
        },
        context_instance=RequestContext(request)
    )

def label_main(request, label_id):
    """
    Main page for a particular label
    """

    label = get_object_or_404(Label, id=label_id)

    return render_to_response('annotations/label_main.html', {
            'label': label,
            },
            context_instance=RequestContext(request)
    )

def labelset_main(request, source_id):
    """
    Main page for a particular source's labelset
    """

    source = get_object_or_404(Source, id=source_id)
    labelset = source.labelset

    return render_to_response('annotations/labelset_main.html', {
            'source': source,
            'labelset': labelset,
            },
            context_instance=RequestContext(request)
    )

def labelset_list(request):
    """
    Page with a list of all the labelsets
    """

    labelsets = LabelSet.objects.all()

    return render_to_response('annotations/labelset_list.html', {
                'labelsets': labelsets,
                },
                context_instance=RequestContext(request)
    )

def label_list(request):
    """
    Page with a list of all the labels
    """

    labels = Label.objects.all()

    return render_to_response('annotations/label_list.html', {
                'labels': labels,
                },
                context_instance=RequestContext(request)
    )


@permission_required('source_admin', (Source, 'id', 'source_id'))
def annotation_tool(request, image_id, source_id):
    """
    View for the annotation tool.
    Redirect to a view for generating points, if there's no points yet.
    """

    image = get_object_or_404(Image, id=image_id)
    #source = get_object_or_404(Source, Image.objects.get(pk=image_id).source.id)
    source = get_object_or_404(Source, id=source_id)

    metadata = image.metadata

    pointValues = Point.objects.filter(image=image).values(
        'point_number', 'row', 'column')
    annotationValues = Annotation.objects.filter(image=image).values(
        'point__point_number', 'label__name', 'label__code')

    annotations = dict()
    for p in pointValues:
        annotations[p['point_number']] = p
    for a in annotationValues:
        annotations[a['point__point_number']].update(a)

    annotations = list(annotations.values())
    annotations.sort(key=lambda x:x['point_number'])

    # Now we've gotten all the relevant points and annotations
    # from the database, in a list of dicts:
    # [{'point_number':1, 'row':294, 'column':749, 'label__name':'Porites', 'label__code':'Porit'},
    #  {'point_number':2, ...},
    #  ...]

    # Scale the image so it fits with the webpage layout.
    initial_display_width = 950    # Change this according to how it looks on the page
    initial_display_height = (initial_display_width * image.original_height) / image.original_width

    return render_to_response('annotations/annotation_tool.html', {
        'source': source,
        'image': image,
        'metadata': metadata,
        'location_values': ', '.join(image.get_location_value_str_list()),
        'annotations': annotations,
        'num_of_points': len(annotations),
        'num_of_annotations': len(annotationValues),
        'initial_display_width': initial_display_width,
        'initial_display_height': initial_display_height,
        },
        context_instance=RequestContext(request)
    )