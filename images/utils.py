# This file contains general utility methods.

import datetime
import math, random
from os.path import splitext
from accounts.utils import get_robot_user
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import Annotation
from images.model_utils import PointGen
from images.models import Point, Metadata, Image, Value1, Value2, Value3, Value4, Value5


def get_location_value_objs(source, valueList, createNewValues=False):
    """
    Takes a list of values as strings:
    ['Shore3', 'Reef 5', 'Loc10']
    Returns a dict of Value objects:
    {'value1': <Value1 object: 'Shore3'>, 'value2': <Value2 object: 'Reef 5'>, ...}

    If the database doesn't have a Value object of the desired name:
    - If createNewValues is True, then the required Value object is
     created and inserted into the DB.
    - If createNewValues is False, then this method returns False.
    """
    valueNameGen = (v for v in valueList)
    valueDict = dict()

    for valueIndex , valueClass in [
            ('value1', Value1),
            ('value2', Value2),
            ('value3', Value3),
            ('value4', Value4),
            ('value5', Value5)
    ]:
        try:
            valueName = valueNameGen.next()
        except StopIteration:
            # That's all the values the valueList had
            break
        else:
            if createNewValues:
                valueDict[valueIndex], created = valueClass.objects.get_or_create(source=source, name=valueName)
            else:
                try:
                    valueDict[valueIndex] = valueClass.objects.get(source=source, name=valueName)
                except valueClass.DoesNotExist:
                    # Value object not found
                    return False

    # All value objects were found/created
    return valueDict


def find_dupe_image(source, values=None, year=None, **kwargs):
    """
    Sees if the given source already has an image with the given arguments.
    """

    # Get Value objects of the value names given in "values".
    valueObjDict = get_location_value_objs(source, values, createNewValues=False)

    if not valueObjDict:
        # One or more of the values weren't found; no dupe image in DB.
        return False

    # Get all the metadata objects in the DB with these location values and year
    metaMatches = Metadata.objects.filter(photo_date__year=year, **valueObjDict)

    # Get the images from our source that have this metadata.
    imageMatches = Image.objects.filter(source=source, metadata__in=metaMatches)

    if len(imageMatches) > 1:
        raise ValueError("Something's not right - this set of metadata has multiple image matches.")
    elif len(imageMatches) == 1:
        return imageMatches[0]
    else:
        return False


def filename_to_metadata(filename, source):
    """
    Takes an image filename without the extension.

    Returns a dict of the location values, and the photo year, month, and day.
    {'values': ['Shore3', 'Reef 5', 'Loc10'],
     'year': 2007, 'month': 8, 'day': 15}
    """

    metadataDict = dict()

    parseError = ValueError('Could not properly extract metadata from the filename "%s".' % filename)
    dateError = ValueError('Invalid date format or values.')
    numOfKeys = source.num_of_keys()

    # value1_value2_..._YYYY-MM-DD
    tokensFormat = ['value'+str(i) for i in range(1, numOfKeys+1)]
    tokensFormat += ['date']
    numTokensExpected = len(tokensFormat)

    # Make a list of the metadata 'tokens' from the filename
    filenameWithoutExt, extension = splitext(filename)
    tokens = filenameWithoutExt.split('_')

    dataTokens = tokens[:numTokensExpected]
    if len(dataTokens) != numTokensExpected:
        raise parseError

    extraTokens = tokens[numTokensExpected:]
    if len(extraTokens) > 0:
        name = '_'.join(extraTokens) + extension
    else:
        name = filename

    # Encode the filename data into a dictionary: {'value1':'Shore2', 'date':'2008-12-18', ...}
    filenameData = dict(zip(tokensFormat, dataTokens))

    valueList = [filenameData['value'+str(i)] for i in range(1, numOfKeys+1)]
    dateToken = filenameData['date']

    try:
        year, month, day = dateToken.split("-")
    except ValueError:
        raise dateError
    # YYYYMMDD parsing:
#    if len(dateToken) != 8:
#        raise dateError
#    year, month, day = dateToken[:4], dateToken[4:6], dateToken[6:8]

    try:
        datetime.date(int(year), int(month), int(day))
    except ValueError:
        # Either non-integer date params, or date params are
        # out of valid range (e.g. month 13)
        raise dateError

    metadataDict['values'] = valueList

    metadataDict['year'] = year
    metadataDict['month'] = month
    metadataDict['day'] = day

    metadataDict['name'] = name

    return metadataDict


def metadata_to_filename(values=None,
                         year=None, month=None, day=None):
    """
    Takes metadata arguments and returns a filename (without the extension)
    which would generate these arguments.
    """

    dateStr = '-'.join([year, month, day])
    filename = '_'.join(values + [dateStr])

    return filename


def get_first_image(source, conditions=None):
    """
    Gets the first image in the source.
    Ordering is done by photo_date's year, then by
    location value 1, ..., location value n.

    conditions:
    A dict specifying additional filters.

    *** WARNING ***
    The use of extra() on querysets involves database-specific arguments!
    For example, MySQL and PostgreSQL may have to use different arguments.
    """
    db_extra_select = {'year': 'YEAR(photo_date)'}  # YEAR() is MySQL only, PostgreSQL has different syntax

    metadatas = Metadata.objects.filter(image__source=source).extra(select=db_extra_select)

    if conditions:
        filter_kwargs = dict()
        for key, value in conditions.iteritems():
            filter_kwargs['image__'+key] = value
        metadatas = metadatas.filter(**filter_kwargs)

    if not metadatas:
        return None

    sort_keys = ['year'] + source.get_value_field_list()
    metadatas_ordered = metadatas.order_by(*sort_keys)

    return Image.objects.get(metadata=metadatas_ordered[0])


def get_prev_or_next_image(current_image, kind, conditions=None):
    """
    Gets the previous or next image in this image's source.

    conditions:
    A list specifying additional filters. For example, 'needs_human_annotation'.

    *** WARNING ***
    The use of extra() on querysets involves database-specific arguments!
    """
    db_extra_select = {'year': 'YEAR(photo_date)'}  # YEAR() is MySQL only, PostgreSQL has different syntax

    metadatas = Metadata.objects.filter(image__source=current_image.source).extra(select=db_extra_select)

    if conditions:
        filter_kwargs = dict()
        for key, value in conditions.iteritems():
            filter_kwargs['image__'+key] = value
        metadatas = metadatas.filter(**filter_kwargs)

    sort_keys = ['year'] + [vf+'__name' for vf in current_image.source.get_value_field_list()]
    sort_keys_reverse = sort_keys[::-1]
    self_metadata_values = Metadata.objects.filter(pk=current_image.metadata.id).extra(select=db_extra_select).values(*sort_keys)[0]

    # If we have 3 sort keys, and are getting the next image, then the algorithm is:
    # - Look for metadatas where key 1 is equal, key 2 is equal, and key 3 is greater
    # - If no matches, look where key 1 is equal and key 2 is greater
    # - If no matches, look where key 1 is greater
    # - Whenever there are matches, get the first one (the matches should be ordered,
    #   so this should be the next image). If no matches in any step, return None.

    if kind == 'next':
        compare_query_str = '{0}__gt'
        metadatas_ordered = metadatas.order_by(*sort_keys)
    else:  # 'prev'
        compare_query_str = '{0}__lt'
        metadatas_ordered = metadatas.order_by(*['-'+sk for sk in sort_keys])

    matching_sort_keys = sort_keys[:]
    for sort_key_to_compare in sort_keys_reverse:
        kwargs = dict()
        del matching_sort_keys[-1]

        for sort_key in matching_sort_keys:
            if sort_key == 'year':
                # For some reason, filter() doesn't seem to care about extra values obtained
                # with extra().  So instead of the 'year' extra value, we need to give
                # something that filter() understands.
                kwargs['photo_date__year'] = self_metadata_values[sort_key]
            else:
                kwargs[sort_key] = self_metadata_values[sort_key]

        if sort_key_to_compare == 'year':
            # And accommodating filter() is even nastier here.
            if kind == 'next':
                kwargs['photo_date__gte'] = datetime.datetime(self_metadata_values['year']+1, 1, 1)
            else:  # 'prev'
                kwargs['photo_date__lt'] = datetime.datetime(self_metadata_values['year'],1,1)
        else:
            kwargs[compare_query_str.format(sort_key_to_compare)] = self_metadata_values[sort_key_to_compare]

        candidate_metadatas = metadatas_ordered.filter(**kwargs)
        if candidate_metadatas:
            return Image.objects.get(metadata=candidate_metadatas[0])

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

    # Find the annotation area.
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


def image_upload_success_message(num_images_uploaded,
                                 num_dupes, dupe_option,
                                 num_annotations):
    """
    Construct the message for a successful image upload operation.
    """
    uploaded_msg = "{num} images uploaded.".format(num=num_images_uploaded)

    if num_dupes > 0:
        if dupe_option == 'replace':
            duplicate_msg = "{num} duplicate images replaced.".format(num=num_dupes)
        else:
            duplicate_msg = "{num} duplicate images skipped.".format(num=num_dupes)
    else:
        duplicate_msg = None

    if num_annotations > 0:
        annotation_msg = "{num} annotations imported.".format(num=num_annotations)
    else:
        annotation_msg = None

    return ' '.join([msg for msg in [uploaded_msg, duplicate_msg, annotation_msg]
                     if msg is not None])