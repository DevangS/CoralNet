from django.shortcuts import render_to_response

def source_select_form(request):
    return render_to_response('source_select_form.html')

def visualize_form(request, source):
    sourceobj = get_object_or_404()
    value1s = Value1.objects.filter(source=source)