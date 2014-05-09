from django.contrib.auth.models import User
from accounts.utils import get_robot_user, is_robot_user
from annotations.models import Annotation
from images.model_utils import PointGen
from images.models import Image, Point, Robot
import images.task_utils as task_utils

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

def get_machine_suggestions_for_image(image_id):
    """
    :param image_id: id of the image to get machine suggestions for.
    :return: suggestions as a list of {label: <label code>,
        score: <score as an integer string>} dicts,
        ordered by confidence.
    """
    img = Image.objects.get(pk=image_id)

    if not img.status.annotatedByRobot:
        return None

    points = Point.objects.filter(image=img).values()
    labels = img.source.labelset.labels.all()
    # Prefetch the labels
    labels_list = list(labels)

    row_col_dicts = task_utils.read_row_col_file(image_id)
    all_points_label_ids_and_scores = task_utils.read_label_score_file(image_id)

    # Convert label ids to label codes
    all_points_label_scores = []
    for label_ids_and_scores in all_points_label_ids_and_scores:
        label_scores = []
        for d in label_ids_and_scores:
            label_id = d['label']
            # TODO: What if the label isn't in the labelset?
            label_obj = labels.get(pk=label_id)
            label_scores.append(
                dict(label=label_obj.code, score=d['score'])
            )
        all_points_label_scores.append(label_scores)

    row_col_to_label_scores = dict()
    for row_col_d, label_scores in zip(row_col_dicts, all_points_label_scores):
        key = str(row_col_d['row']) + ',' + str(row_col_d['column'])
        row_col_to_label_scores[key] = label_scores

    suggestions_for_all_points = dict()
    for pt in points:
        key = str(pt['row']) + ',' + str(pt['column'])
        # TODO: What if there is no entry for this row and column?
        suggestions_for_all_points[pt['point_number']] = row_col_to_label_scores[key]

    return suggestions_for_all_points

