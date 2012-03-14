from django.contrib.auth.models import User
from accounts.utils import get_robot_user, is_robot_user
from annotations.models import Annotation
from images.model_utils import PointGen
from images.models import Image, Point, Robot

def image_annotation_all_done(image_id):

    image = Image.objects.get(id=image_id)
    annotations = Annotation.objects.filter(image=image)

    # If every point has an annotation, and all annotations are by humans,
    # then we're all done
    return (annotations.count() == Point.objects.filter(image=image).count()
            and annotations.filter(user=get_robot_user()).count() == 0)

def image_has_any_human_annotations(image_id):
    """
    Return True if the image has at least one human-made Annotation.
    Return False otherwise.
    """
    image = Image.objects.get(id=image_id)
    human_annotations = Annotation.objects.filter(image=image).exclude(user=get_robot_user())
    return human_annotations.count() > 0

def image_annotation_area_is_editable(image_id):
    """
    Returns True if the image's annotation area is editable; False otherwise.
    The annotation area is editable only if:
    (1) there are no human annotations for the image yet, and
    (2) the points are not imported.
    """
    image = Image.objects.get(id=image_id)
    return (not image_has_any_human_annotations(image_id))\
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