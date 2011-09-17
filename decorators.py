from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.functional import wraps
from images.models import Source

def labelset_required(source_id_view_arg, message):
    """
    Decorator for views that makes sure the source has a labelset.  If
    not, then the view isn't shown and we instead show a simple template
    saying that a labelset must be created.

    This decorator code is based on the Guardian decorator code.

    :param source_id_view_arg: a string that specifies the name of the view method
      argument that corresponds to the source id.
    :param message: a message to be displayed on the template if the source
      doesn't have a labelset.

    Examples::

        @labelset_required('source_id', 'Your source needs a labelset before you can import annotations.')
        def import_annotations(request, source_id):
            return HttpResponse('An HTTP response')
    """

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):

            if source_id_view_arg not in kwargs:
                raise ValueError("Argument %s was not passed "
                    "into view function" % source_id_view_arg)
            source_id = kwargs[source_id_view_arg]

            source = Source.objects.get(pk=source_id)

            if source.labelset.isEmptyLabelset():
                return render_to_response('annotations/labelset_required.html', {
                    'message': message,
                    'source': source,
                    },
                    context_instance=RequestContext(request)
                    )
            
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return decorator