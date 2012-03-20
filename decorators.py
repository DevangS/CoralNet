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
from annotations.utils import image_annotation_area_is_editable

from images.models import Source, Image

# TODO: Add comments to this class.
class ModelViewDecorator():
    """
    Class for instantiating decorators for views.
    Specifically, views that take the id of a model as a parameter.

    :param model_class:
    :param meets_requirements:
    :param template:
    :param get_extra_context:
    :param default_message:
    """

    def __init__(self, model_class, meets_requirements,
                 template, get_extra_context=None,
                 default_message=None):
        self.model_class = model_class
        self.meets_requirements = meets_requirements
        self.template = template
        self.get_extra_context = get_extra_context
        self.default_message = default_message

    def __call__(self, object_id_view_arg, message=None, **requirements_kwargs):
        def decorator(view_func):
            def _wrapped_view(request, *args, **kwargs):

                if object_id_view_arg not in kwargs:
                    raise ValueError("Argument %s was not passed "
                                     "into view function" % object_id_view_arg)
                object_id = kwargs[object_id_view_arg]

                object = get_object_or_404(self.model_class, pk=object_id)

                if not self.meets_requirements(object, request, **requirements_kwargs):
                    context_dict = dict(
                        message=message or self.default_message or ""
                    )
                    if self.get_extra_context:
                        context_dict.update(self.get_extra_context(object))

                    return render_to_response(self.template,
                        context_dict,
                        context_instance=RequestContext(request)
                    )

                return view_func(request, *args, **kwargs)
            return wraps(view_func)(_wrapped_view)
        return decorator

def image_get_extra_context(image):
    return dict(
        image=image,
        source=image.source,
    )
def source_get_extra_context(source):
    return dict(
        source=source,
    )

# @image_annotation_area_must_be_editable('image_id')
image_annotation_area_must_be_editable = ModelViewDecorator(
    model_class=Image,
    meets_requirements=lambda image, request: image_annotation_area_is_editable(image),
    template='annotations/annotation_area_not_editable.html',
    get_extra_context=image_get_extra_context,
    default_message="This image's annotation area is not editable, because re-generating points "
                    "would result in loss of data (such as annotations made in the annotation tool, "
                    "or points imported from outside the site)."
    )

# @image_labelset_required('image_id')
image_labelset_required = ModelViewDecorator(
    model_class=Image,
    meets_requirements=lambda image, request: not image.source.labelset.isEmptyLabelset(),
    template='annotations/labelset_required.html',
    get_extra_context=image_get_extra_context,
    default_message="You need to create a labelset before you can use this page."
    )

# @source_labelset_required('source_id')
source_labelset_required = ModelViewDecorator(
    model_class=Source,
    meets_requirements=lambda source, request: not source.labelset.isEmptyLabelset(),
    template='annotations/labelset_required.html',
    get_extra_context=source_get_extra_context,
    default_message="You need to create a labelset before you can use this page."
)

# @image_visibility_required('image_id')
image_visibility_required = ModelViewDecorator(
    model_class=Image,
    meets_requirements=lambda image, request: image.source.visible_to_user(request.user),
    template='permission_denied.html',
)

# @source_visibility_required('source_id')
source_visibility_required = ModelViewDecorator(
    model_class=Source,
    meets_requirements=lambda source, request: source.visible_to_user(request.user),
    template='permission_denied.html',
)

# TODO: Make this even more DRY: just pass in 'admin' instead of Source.PermTypes.ADMIN.code.
# @image_permission_required('image_id', perm=Source.PermTypes.<YOUR_PERMISSION_TYPE_HERE>.code)
image_permission_required = ModelViewDecorator(
    model_class=Image,
    meets_requirements=lambda image, request, perm: request.user.has_perm(perm, image.source),
    template='permission_denied.html',
)

# @source_permission_required('source_id', perm=Source.PermTypes.<YOUR_PERMISSION_TYPE_HERE>.code)
source_permission_required = ModelViewDecorator(
    model_class=Source,
    meets_requirements=lambda source, request, perm: request.user.has_perm(perm, source),
    template='permission_denied.html',
)


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
