from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from annotations.forms import NewLabelForm, NewLabelSetForm
from annotations.models import Label, LabelSet

@login_required
def label_new(request):
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
def labelset_new(request):
    if request.method == 'POST':
        form = NewLabelSetForm(request.POST)

        if form.is_valid():
            labelSet = form.save()
            messages.success(request, 'LabelSet successfully created.')
            return HttpResponseRedirect(reverse('labelset_main', args=[labelSet.id]))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NewLabelSetForm()

    return render_to_response('annotations/labelset_new.html', {
        'form': form,
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

def labelset_main(request, labelset_id):
    """
    Main page for a particular labelset
    """

    labelset = get_object_or_404(LabelSet, id=labelset_id)

    return render_to_response('annotations/labelset_main.html', {
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