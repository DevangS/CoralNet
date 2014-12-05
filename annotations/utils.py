import operator

from django.contrib.auth.models import User
from accounts.utils import get_robot_user, is_robot_user, get_alleviate_user
from annotations.models import Annotation
from images.model_utils import PointGen
from images.models import Image, Point, Robot
from images.tasks import get_alleviate_meta

def image_annotation_all_done(image):
    """
    Return True if all of the image's annotation points are human annotated.
    Return False otherwise.
    Don't use the status field annotatedByHuman.  That field depends
    on this function, not the other way around!
    """
    annotations = Annotation.objects.filter(image=image)

    # If every point has an annotation, and all annotations are by humans,
    # then we're all done
    return (annotations.count() == Point.objects.filter(image=image).count()
            and annotations.filter(user=get_robot_user()).count() == 0)

def image_has_any_human_annotations(image):
    """
    Return True if the image has at least one human-made Annotation.
    Return False otherwise.
    """
    human_annotations = Annotation.objects.filter(image=image).exclude(user=get_robot_user())
    return human_annotations.count() > 0

def image_annotation_area_is_editable(image):
    """
    Returns True if the image's annotation area is editable; False otherwise.
    The annotation area is editable only if:
    (1) there are no human annotations for the image yet, and
    (2) the points are not imported.
    """
    return (not image_has_any_human_annotations(image))\
    and (PointGen.db_to_args_format(image.point_generation_method)['point_generation_type'] != PointGen.Types.IMPORTED)

def get_annotation_user_display(anno):
    """
    anno - an annotations.Annotation model.

    Returns a string representing the user who made the annotation.
    """

    if not anno.user:
        return "(Unknown user)"

    elif is_robot_user(anno.user):
        if not anno.robot_version:
            return "(Robot, unknown version)"
        return "Robot: %s" % anno.robot_version

    else:
        return anno.user.username

def get_annotation_version_user_display(anno_version):
    """
    anno - a reversion.Version model; a previous or current version of an annotations.Annotation model.

    Returns a string representing the user who made the annotation.
    """

    user_id = anno_version.field_dict['user']
    user = User.objects.get(pk=user_id)

    if not user:
        return "(Unknown user)"

    elif is_robot_user(user):
        # This check may be needed because Annotation didn't originally save robot versions.
        if not anno_version.field_dict.has_key('robot_version'):
            return "(Robot, unknown version)"

        robot_version_id = anno_version.field_dict['robot_version']
        if not robot_version_id:
            return "(Robot, unknown version)"

        robot_version = Robot.objects.get(pk=robot_version_id)
        return "Robot: %s" % robot_version

    else:
        return user.username


def apply_alleviate(image_id, label_probabilities):
    """
    Apply alleviate to a particular image: auto-accept top machine suggestions
    based on the confidence threshold.

    :param image_id: id of the image.
    :param label_probabilities: the machine's assigned label
           probabilities for each point of the image.
    :return: nothing.
    """
    img = Image.objects.get(id=image_id)
    source = img.source
    robot = source.get_latest_robot()
    alleviate_meta = get_alleviate_meta(robot) 

    if source.alleviate_threshold < 1:
        return
    if (not(alleviate_meta['ok'])):
        return

    if (source.alleviate_threshold == 100):
        # if the user wants 100% alleviation, we set the threhold to 0, meaning that all points will be annotated.
        confidenct_threshold = 0
    else:
        # this is a critical step in the alleviate logic. It translate the alleviate level to a confidence threshold for the classifier.
        # this confidence threshold is between 0 and 1.
        confidenct_threshold = alleviate_meta['score_translate'][source.alleviate_threshold]

    machine_annos = Annotation.objects.filter(image=img, user=get_robot_user())
    alleviate_was_applied = False

    for anno in machine_annos:
        pt_number = anno.point.point_number
        label_scores = label_probabilities[pt_number]
        descending_scores = sorted(label_scores, key=operator.itemgetter('score'), reverse=True)
        top_score = descending_scores[0]['score']
        top_confidence = top_score

        if top_confidence >= confidenct_threshold:
            # Save the annotation under the username Alleviate, so that it's no longer
            # a robot annotation.
            anno.user = get_alleviate_user()
            anno.save()
            alleviate_was_applied = True

    if alleviate_was_applied:
        # Are all points human annotated now?
        all_done = image_annotation_all_done(img)
        # Update image status, if needed
        if all_done:
            img.status.annotatedByHuman = True
            img.status.save()


