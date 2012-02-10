# Much of this decorator code is based on the Guardian decorator code.
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

from django.db.models import Model, get_model
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template.context import RequestContext
from django.utils.functional import wraps
from django.utils.http import urlquote
from guardian.exceptions import GuardianError

from images.models import Source

def labelset_required(source_id_view_arg, message):
    """
    Decorator for views that makes sure the source has a labelset.  If
    not, then the view isn't shown and we instead show a simple template
    saying that a labelset must be created.

    :param source_id_view_arg: a string that specifies the name of the view method
      argument that corresponds to the source id.
    :param message: a message to be displayed on the template if the source
      doesn't have a labelset.

    Example::

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


def permission_required(perm, lookup_variables=None, **kwargs):
    """
    Generic decorator for views that require permissions.

    Near-carbon copy of Guardian's permission_required, except this
    redirects to our custom template.  (Yes, the code duplication
    is awful, sorry)
    """
    login_url = kwargs.pop('login_url', settings.LOGIN_URL)
    redirect_field_name = kwargs.pop('redirect_field_name', REDIRECT_FIELD_NAME)

    # Check if perm is given as string in order not to decorate
    # view function itself which makes debugging harder
    if not isinstance(perm, basestring):
        raise GuardianError("First argument must be in format: "
            "'app_label.codename or a callable which return similar string'")

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # if more than one parameter is passed to the decorator we try to
            # fetch object for which check would be made
            obj = None
            if lookup_variables:
                model, lookups = lookup_variables[0], lookup_variables[1:]
                # Parse model
                if isinstance(model, basestring):
                    splitted = model.split('.')
                    if len(splitted) != 2:
                        raise GuardianError("If model should be looked up from "
                            "string it needs format: 'app_label.ModelClass'")
                    model = get_model(*splitted)
                elif type(model) in (Model, ModelBase, QuerySet):
                    pass
                else:
                    raise GuardianError("First lookup argument must always be "
                        "a model, string pointing at app/model or queryset. "
                        "Given: %s (type: %s)" % (model, type(model)))
                # Parse lookups
                if len(lookups) % 2 != 0:
                    raise GuardianError("Lookup variables must be provided "
                        "as pairs of lookup_string and view_arg")
                lookup_dict = {}
                for lookup, view_arg in zip(lookups[::2], lookups[1::2]):
                    if view_arg not in kwargs:
                        raise GuardianError("Argument %s was not passed "
                            "into view function" % view_arg)
                    lookup_dict[lookup] = kwargs[view_arg]
                obj = get_object_or_404(model, **lookup_dict)

            # Check if the user is logged in
            if not request.user.is_authenticated():
                path = urlquote(request.get_full_path())
                tup = login_url, redirect_field_name, path
                return HttpResponseRedirect("%s?%s=%s" % tup)
            # Check if the user has any permissions in this source
            # Handles both permission checks--original and with object provided--
            # because ``obj`` defaults to None
            elif not request.user.has_perm(perm, obj):
                return render_to_response('permission_denied.html', {
                    },
                    context_instance=RequestContext(request)
                    )
            # User has permission, so show the requested page.
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return decorator


def visibility_required(source_id_view_arg):
    """
    View decorator: requires that the user has permission to see the Source.
    If not, then the view isn't shown and we instead show a simple template
    saying that they don't have permission to access the page.

    :param source_id_view_arg: a string that specifies the name of the view method
      argument that corresponds to the source id.
    :param message: a message to be displayed on the template if the source
      doesn't have a labelset.

    Example::

        @visibility_required('source_id')
        def source_main(request, source_id):
            return HttpResponse('An HTTP response')
    """

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):

            if source_id_view_arg not in kwargs:
                raise ValueError("Argument %s was not passed "
                    "into view function" % source_id_view_arg)
            source_id = kwargs[source_id_view_arg]

            source = Source.objects.get(pk=source_id)

            if not source.visible_to_user(request.user):
                return render_to_response('permission_denied.html', {
                    },
                    context_instance=RequestContext(request)
                    )

            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return decorator