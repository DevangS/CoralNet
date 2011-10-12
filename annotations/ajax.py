from dajaxice.decorators import dajaxice_register
from django.contrib.auth.models import User
from django.utils import simplejson
from annotations.models import Label, Annotation
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
        return simplejson.dumps("User id error")
    if not user.has_perm(Source.PermTypes.EDIT.code, image.source):
        return simplejson.dumps("Image id error")

    # Get stuff from the DB in advance, see if it saves time
    pointsList = list(Point.objects.filter(image=image))
    points = dict([ (p.point_number, p) for p in pointsList ])

    annotationsList = list(Annotation.objects.filter(user=user, image=image, source=source))
    annotations = dict([ (a.point_id, a) for a in annotationsList ])

    for name, value in formDict.iteritems():

        if name.startswith('label_'):

            # Get this annotation's point
            pointNum = name[len('label_'):]   # The part after 'label_'
            point = points[int(pointNum)]

            # Get the label that the form field value refers to.
            # Anticipate errors, even if we plan to check input with JS.
            labelCode = value
            if labelCode == '':
                label = None
            else:
                labels = Label.objects.filter(code=labelCode)
                if len(labels) == 0:
                    return simplejson.dumps("No label with code %s." % labelCode)

                label = labels[0]
                if label not in sourceLabels:
                    return simplejson.dumps("The labelset has no label with code %s." % labelCode)

            if annotations.has_key(point.id):
                anno = annotations[point.id]
                if label is None:
                    anno.delete()
                elif label != anno.label:
                    anno.label = label
                    anno.save()
            else:
                if label is not None:
                    newAnno = Annotation(point=point, user=user, image=image, source=source, label=label)
                    newAnno.save()

    return simplejson.dumps(False)
