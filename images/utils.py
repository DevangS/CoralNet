# This file contains general utility methods.

import datetime
import math, random
from accounts.utils import get_robot_user
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import Annotation
from lib.exceptions import *
from images.model_utils import PointGen
from images.models import Point, Metadata, Image, Value1, Value2, Value3, Value4, Value5


def get_location_value_objs(source, value_names, createNewValues=False):
    """
    Takes a list of values as strings:
    ['Shore3', 'Reef 5', 'Loc10']
    Returns a dict of Value objects:
    {'value1': <Value1 object: 'Shore3'>, 'value2': <Value2 object: 'Reef 5'>, ...}

    If the database doesn't have a Value object of the desired name:
    - If createNewValues is True, then the required Value object is
     created and inserted into the DB.
    - If createNewValues is False, then this method returns None.
    """

    # Get the value field names and model classes corresponding to
    # the given value_names.
    num_of_location_values = len(value_names)
    value_fields = ['value1', 'value2', 'value3', 'value4', 'value5'][:num_of_location_values]
    value_classes = [Value1, Value2, Value3, Value4, Value5][:num_of_location_values]

    value_dict = dict()

    for value_field, value_class, value_name in zip(value_fields, value_classes, value_names):

        if value_name == '':

            # Don't allow empty-string values. The empty or null value is
            # represented by having no Value object at all.
            value_dict[value_field] = None

        else:

            # Non-empty value.

            if createNewValues:
                # Get the Value object if there is one, or create it otherwise.
                value_dict[value_field], created = value_class.objects.get_or_create(
                    source=source, name=value_name
                )
            else:
                try:
                    # Get the Value object if there is one.
                    value_dict[value_field] = value_class.objects.get(
                        source=source, name=value_name
                    )
                except value_class.DoesNotExist:
                    # Value object not found, and can't create it.
                    # Can't return a valueDict.
                    raise ValueObjectNotFoundError

    # All the desired Value objects were found/created.
    return value_dict


def get_first_image(source, conditions=None):
    """
    Gets the first image in the source.
    Ordering is done by image id.

    conditions:
    A dict specifying additional filters.
    """
    imgs = Image.objects.filter(source=source)

    if conditions:
        filter_kwargs = dict()
        for key, value in conditions.iteritems():
            filter_kwargs[key] = value
        imgs = imgs.filter(**filter_kwargs)

    if not imgs:
        return None

    imgs_ordered = imgs.order_by('pk')

    return imgs_ordered[0]


def get_prev_or_next_image(current_image, kind, conditions=None):
    """
    Gets the previous or next image in this image's source.

    conditions:
    A list specifying additional filters. For example, 'needs_human_annotation'.
    """
    imgs = Image.objects.filter(source=current_image.source)

    if conditions:
        filter_kwargs = dict()
        for key, value in conditions.iteritems():
            filter_kwargs[key] = value
        imgs = imgs.filter(**filter_kwargs)

    if kind == 'prev':
        # Order imgs so that highest pk comes first.
        # Then keep only the imgs with pk less than this image.
        imgs_ordered = imgs.order_by('-pk')
        candidate_imgs = imgs_ordered.filter(pk__lt=current_image.pk)
    else: # next
        # Order imgs so that lowest pk comes first.
        # Then keep only the imgs with pk greater than this image.
        imgs_ordered = imgs.order_by('pk')
        candidate_imgs = imgs_ordered.filter(pk__gt=current_image.pk)

    if candidate_imgs:
        return candidate_imgs[0]
    else:
        # No matching images before this image (if requesting prev) or
        # after this image (if requesting next).
        return None


def get_next_image(current_image, conditions=None):
    """
    Get the "next" image in the source.
    Return None if the current image is the last image.
    """
    return get_prev_or_next_image(current_image, 'next', conditions=conditions)

def get_prev_image(current_image, conditions=None):
    """
    Get the "previous" image in the source.
    Return None if the current image is the first image.
    """
    return get_prev_or_next_image(current_image, 'prev', conditions=conditions)


def calculate_points(img,
                     annotation_area=None,
                     point_generation_type=None,
                     simple_number_of_points=None,
                     number_of_cell_rows=None,
                     number_of_cell_columns=None,
                     stratified_points_per_cell=None
):
    """
    Calculate points for this image. This doesn't actually
    insert anything in the database; it just generates the
    row, column for each point number.

    Returns the points as a list of dicts; each dict
    represents a point, and has keys "row", "column",
    and "point_number".
    """

    points = []

    annoarea_min_col = annotation_area['min_x']
    annoarea_max_col = annotation_area['max_x']
    annoarea_min_row = annotation_area['min_y']
    annoarea_max_row = annotation_area['max_y']

    annoarea_height = annoarea_max_row - annoarea_min_row + 1
    annoarea_width = annoarea_max_col - annoarea_min_col + 1


    if point_generation_type == PointGen.Types.SIMPLE:

        simple_random_points = []

        for i in range(simple_number_of_points):
            row = random.randint(annoarea_min_row, annoarea_max_row)
            column = random.randint(annoarea_min_col, annoarea_max_col)

            simple_random_points.append({'row': row, 'column': column})

        # To make consecutive points appear reasonably close to each other, impose cell rows
        # and cols, then make consecutive points fill the cells one by one.
        NUM_OF_CELL_ROWS = 5
        NUM_OF_CELL_COLUMNS = 5
        cell = dict()
        for r in range(NUM_OF_CELL_ROWS):
            cell[r] = dict()
            for c in range(NUM_OF_CELL_COLUMNS):
                cell[r][c] = []

        for p in simple_random_points:
            # Assign each random point to the cell it belongs in.
            # This is all int math, so no floor(), int(), etc. needed.
            # But remember to not divide until the end.
            r = ((p['row'] - annoarea_min_row) * NUM_OF_CELL_ROWS) / annoarea_height
            c = ((p['column'] - annoarea_min_col) * NUM_OF_CELL_COLUMNS) / annoarea_width

            cell[r][c].append(p)

        point_num = 1
        for r in range(NUM_OF_CELL_ROWS):
            for c in range(NUM_OF_CELL_COLUMNS):
                for p in cell[r][c]:

                    points.append(dict(row=p['row'], column=p['column'], point_number=point_num))
                    point_num += 1

    elif point_generation_type == PointGen.Types.STRATIFIED:

        point_num = 1

        # Each pixel of the annotation area goes in exactly one cell.
        # Cell widths and heights are within one pixel of each other.
        for row_num in range(0, number_of_cell_rows):
            row_min = ((row_num * annoarea_height) / number_of_cell_rows) + annoarea_min_row
            row_max = (((row_num+1) * annoarea_height) / number_of_cell_rows) + annoarea_min_row - 1

            for col_num in range(0, number_of_cell_columns):
                col_min = ((col_num * annoarea_width) / number_of_cell_columns) + annoarea_min_col
                col_max = (((col_num+1) * annoarea_width) / number_of_cell_columns) + annoarea_min_col - 1

                for cell_point_num in range(0, stratified_points_per_cell):
                    row = random.randint(row_min, row_max)
                    column = random.randint(col_min, col_max)

                    points.append(dict(row=row, column=column, point_number=point_num))
                    point_num += 1

    elif point_generation_type == PointGen.Types.UNIFORM:

        point_num = 1

        for row_num in range(0, number_of_cell_rows):
            row_min = ((row_num * annoarea_height) / number_of_cell_rows) + annoarea_min_row
            row_max = (((row_num+1) * annoarea_height) / number_of_cell_rows) + annoarea_min_row - 1
            row_mid = int(math.floor( (row_min+row_max) / 2.0 ))

            for col_num in range(0, number_of_cell_columns):
                col_min = ((col_num * annoarea_width) / number_of_cell_columns) + annoarea_min_col
                col_max = (((col_num+1) * annoarea_width) / number_of_cell_columns) + annoarea_min_col - 1
                col_mid = int(math.floor( (col_min+col_max) / 2.0 ))

                points.append(dict(row=row_mid, column=col_mid, point_number=point_num))
                point_num += 1

    return points


def generate_points(img):
    """
    Generate annotation points for the Image img,
    and delete any points that had previously existed.

    Does nothing if the image already has human annotations,
    because we don't want to delete any human work.
    """

    # If there are any human annotations for this image,
    # abort point generation.
    human_annotations = Annotation.objects.filter(image=img).exclude(user=get_robot_user())
    if human_annotations:
        return

    # Find the annotation area, expressed in pixels.
    d = AnnotationAreaUtils.db_format_to_numbers(img.metadata.annotation_area)
    annoarea_type = d.pop('type')
    if annoarea_type == AnnotationAreaUtils.TYPE_PERCENTAGES:
        annoarea_dict = AnnotationAreaUtils.percentages_to_pixels(width=img.original_width, height=img.original_height, **d)
    elif annoarea_type == AnnotationAreaUtils.TYPE_PIXELS:
        annoarea_dict = d
    else:
        raise ValueError("Can't generate points with annotation area type '{0}'.".format(annoarea_type))

    # Calculate points.
    new_points = calculate_points(
        img, annotation_area=annoarea_dict,
        **PointGen.db_to_args_format(img.source.default_point_generation_method)
    )

    # Delete old points for this image, if any.
    old_points = Point.objects.filter(image=img)
    for old_point in old_points:
        old_point.delete()

    # Save the newly calculated points.
    for new_point in new_points:
        Point(row=new_point['row'],
              column=new_point['column'],
              point_number=new_point['point_number'],
              image=img,
        ).save()

    # Update image status.
    # Make sure the image goes through the feature-making step again.
    status = img.status
    status.hasRandomPoints = True
    status.save()
