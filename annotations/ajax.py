from dajaxice.decorators import dajaxice_register
from django.contrib.auth.models import User
from django.utils import simplejson
from accounts.utils import is_robot_user
from annotations.models import Label, Annotation
from annotations.utils import image_annotation_all_done
from images.models import Image, Point, Source

@dajaxice_register
def ajax_save_annotations(request, annotationForm):
    """
    Called via Ajax from the annotation tool form, if the user clicked
    the "Save Annotations" button.

    Takes: the annotation form field names and values, serialized with jQuery's serializeArray()
    Does: saves the annotations in the database
    Returns: false if successful, an error string if there was a problem
    """

    #TODO: just use request.POST instead of the annotationForm parameter
    formDict = dict([ (d['name'], d['value']) for d in annotationForm ])

    image = Image.objects.get(pk=formDict['image_id'])
    user = User.objects.get(pk=formDict['user_id'])
    source = image.source
    sourceLabels = source.labelset.labels.all()

    # Sanity checks
    if user != request.user:
        return simplejson.dumps(dict(error="User id error"))
    if not user.has_perm(Source.PermTypes.EDIT.code, image.source):
        return simplejson.dumps(dict(error="Image id error"))

    # Get stuff from the DB in advance, should save time
    pointsList = list(Point.objects.filter(image=image))
    points = dict([ (p.point_number, p) for p in pointsList ])

    annotationsList = list(Annotation.objects.filter(image=image, source=source))
    annotations = dict([ (a.point_id, a) for a in annotationsList ])

    for name, value in formDict.iteritems():

        if name.startswith('label_'):

            # Get this annotation's point
            pointNum = name[len('label_'):]   # The part after 'label_'
            point = points[int(pointNum)]

            # Does the form field have a non-human-confirmed robot annotation?
            isFormRobotAnnotation = simplejson.loads(formDict['robot_' + pointNum])

            # Get the label that the form field value refers to.
            # Anticipate errors, even if we plan to check input with JS.
            labelCode = value
            if labelCode == '':
                label = None
            else:
                labels = Label.objects.filter(code=labelCode)
                if len(labels) == 0:
                    return simplejson.dumps(dict(error="No label with code %s." % labelCode))

                label = labels[0]
                if label not in sourceLabels:
                    return simplejson.dumps(dict(error="The labelset has no label with code %s." % labelCode))

            # An annotation of this point number exists in the database
            if annotations.has_key(point.id):
                anno = annotations[point.id]
                # Label field is now blank.
                # We're not allowing label deletions, so don't do anything in this case.
                if label is None:
                    pass
                # Label was robot annotated, and then the human user confirmed or changed it
                elif is_robot_user(anno.user) and not isFormRobotAnnotation:
                    anno.label = label
                    anno.user = user
                    anno.save()
                # Label was otherwise changed
                elif label != anno.label:
                    anno.label = label
                    anno.user = user
                    anno.save()

            # No annotation of this point number in the database yet
            else:
                if label is not None:
                    newAnno = Annotation(point=point, user=user, image=image, source=source, label=label)
                    newAnno.save()

    if image_annotation_all_done(image.id):
        # Image annotation is all done
        if not image.status.annotatedByHuman:
            image.status.annotatedByHuman = True
            image.status.save()
        # (Need simplejson.dumps() to convert the Python True to a JS true)
        return simplejson.dumps(dict(all_done=True))
    else:
        # Not done
        if image.status.annotatedByHuman:
            image.status.annotatedByHuman = False
            image.status.save()
        return dict()

    
@dajaxice_register
def ajax_is_all_done(request, image_id):
    return simplejson.dumps(image_annotation_all_done(image_id))

