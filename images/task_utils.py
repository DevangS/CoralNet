import os
from django.conf import settings
from images.models import Image, Point
from annotations.models import Label
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins

# TODO: Figure out how to avoid duplicating these filepaths between tasks.py
# and task_utils.py. Perhaps anything reading the raw filenames should just
# go in one file or the other?
join_processing_root = lambda *p: os.path.join(settings.PROCESSING_ROOT, *p)
FEATURES_DIR = join_processing_root("images/features/")
CLASSIFY_DIR = join_processing_root("images/classify/")


def read_row_col_file(image_id):
    filename = os.path.join(FEATURES_DIR, str(image_id) + "_rowCol.txt")
    f = open(filename, 'r')

    dicts = []
    for line in f:
        row, column = line.strip().split(',')
        dicts.append(dict(
            row=int(row),
            column=int(column),
        ))

    f.close()
    return dicts

def read_label_score_file(image_id):
    """
    Read the label scores file, which contains the machine-assigned
    score of each label for each point of the image.
    e.g. for point 1, label A has score 20, label B has score 5
    and so on for each label.

    :param image_id: id of the image to get label probabilities for.
    :return: list of list of dicts. [[{label: <label id>, score: <score>}, ...], ...]
      OR, None if the file can't be found.
    """
    img = Image.objects.get(pk=image_id)
    filename = os.path.join(
        CLASSIFY_DIR, str(image_id) + "_" + img.get_process_date_short_str() + ".txt.prob"
    )
    try:
        f = open(filename, 'r')
    except IOError:
        return None

    # Labels line example: labels 2 3 4 1 5 13 6 7 8
    # Where the numbers are the ids of the labels that can be chosen from.
    labels_line = f.readline().strip()
    label_ids = labels_line.split(' ')[1:]

    # Other lines example: 5 0.0500984 0.13629 0.208848 0.0387356
    # 0.326232 0.0506014 0.0337545 0.122562 0.0328777
    #
    # Where 5 is the label id of the highest-score label,
    # and the other numbers are the scores of each label,
    # in the same order as the labels line's ids.
    label_score_lists = []
    for line in f:
        tokens = line.strip().split(' ')
        label_scores = [float(t) for t in tokens[1:]]
        id_prob_tuples = zip(label_ids, label_scores)
        label_score_lists.append(
            [dict(label=t[0], score=t[1]) for t in id_prob_tuples]
        )

    f.close()
    return label_score_lists


def get_label_probabilities_for_image(image_id):
    """
    :param image_id: id of the image to get label probabilities for.
    :return:
        (A) full label probabilities for an image. A dict of point numbers
        to label-probability mappings. For example:
        {1: [{'Acrop', 0.148928}, {'Porit', 0.213792}, ...], 2: [...], ...}
        OR
        (B) None, if there was a problem getting the probabilities
        (e.g. some label ids or rows/cols didn't match for some reason,
        or the label probabilities file couldn't be found).
    """
    img = Image.objects.get(pk=image_id)

    points = Point.objects.filter(image=img).values()
    labels = img.source.labelset.labels.all()
    # Prefetch the labels
    labels_list = list(labels)

    row_col_dicts = read_row_col_file(image_id)
    all_points_label_ids_and_scores = read_label_score_file(image_id)

    # Check for problems reading the files.
    # TODO: It would be good to have some form of logging that happens
    # in this case (not just throwing an error at the user).
    if all_points_label_ids_and_scores is None:
        return None

    # Convert label ids to label codes
    all_points_label_scores = []
    for label_ids_and_scores in all_points_label_ids_and_scores:
        label_scores = []
        for d in label_ids_and_scores:
            label_id = d['label']
            try:
                label_obj = labels.get(pk=label_id)
            except ObjectDoesNotExist, e:
                # if we can't find the label in the labelset we return None. TODO: this seems like sort of a hack.
                mail_admins('Label match error', 'Error in matching label ' + str(label_id) + ' from image ' + str(image_id) + ' to the labelset. Error message: ' + str(e))
                return None
            label_scores.append(
                dict(label=label_obj.code, score=d['score'])
            )
        all_points_label_scores.append(label_scores)

    # Make a dict of row-col pairs to label scores
    row_col_to_label_scores = dict()
    for row_col_d, label_scores in zip(row_col_dicts, all_points_label_scores):
        key = str(row_col_d['row']) + ',' + str(row_col_d['column'])
        row_col_to_label_scores[key] = label_scores

    # Go from row-col pairs to points;
    # this gets a dict from point numbers to label scores
    probabilities_for_all_points = dict()
    for pt in points:
        key = str(pt['row']) + ',' + str(pt['column'])
        try:
            probabilities_for_all_points[pt['point_number']] = row_col_to_label_scores[key]
        except KeyError, e:
            mail_admins('Annotation tool error', 'Cant match the row, col location to a point number -reason: ' + str(e))
            return None

    return probabilities_for_all_points