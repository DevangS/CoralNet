import os
from django.conf import settings
from images.models import Image


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
    """
    img = Image.objects.get(pk=image_id)
    filename = os.path.join(
        CLASSIFY_DIR, str(image_id) + "_" + img.get_process_date_short_str() + ".txt.prob"
    )
    f = open(filename, 'r')

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