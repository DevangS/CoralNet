import datetime
import os
from os.path import splitext
import shelve
from django.conf import settings
from django.core.urlresolvers import reverse
from accounts.utils import get_imported_user
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import Label, Annotation
from images.model_utils import PointGen
from images.models import Metadata, ImageStatus, Image, Point
from images.utils import  get_location_value_objs, generate_points
from lib import str_consts
from lib.exceptions import DirectoryAccessError, FileContentError, ValueObjectNotFoundError, FilenameError
from CoralNet.utils import rand_string

def get_image_identifier(valueList, year):
    """
    Use the location values and the year to build a string identifier for an image:
    Shore1;Reef5;...;2008
    """
    return ';'.join(valueList + [year])


def annotations_file_to_python(annoFile, source, expecting_labels):
    """
    Takes: an annotations file

    Returns: the Pythonized annotations:
    A dictionary like this:
    {'Shore1;Reef3;...;2008': [{'row':'695', 'col':'802', 'label':'POR'},
                               {'row':'284', 'col':'1002', 'label':'ALG'},
                               ...],
     'Shore2;Reef5;...;2009': [...]
     ... }

    Checks for: correctness of file formatting, i.e. all words/tokens are there on each line
    (will throw an error otherwise)
    """

    # We'll assume annoFile is an InMemoryUploadedFile, as opposed to a filename of a temp-disk-storage file.
    # If we encounter a case where we have a filename, use the below:
    #annoFile = open(annoFile, 'r')

    # Format args: line number, line contents, error message
    file_error_format_str = str_consts.ANNOTATION_FILE_FULL_ERROR_MESSAGE_FMTSTR

    numOfKeys = source.num_of_keys()
    uniqueLabelCodes = []

    # The order of the words/tokens is encoded here.  If the order ever
    # changes, we should only have to change this part.
    words_format_without_label = ['value'+str(i) for i in range(1, numOfKeys+1)]
    words_format_without_label += ['date', 'row', 'col']
    words_format_with_label = words_format_without_label + ['label']

    num_words_with_label = len(words_format_with_label)
    num_words_without_label = len(words_format_without_label)

    # The annotation dict needs to be kept on disk temporarily until all the
    # Ajax upload requests are done. Thus, we'll use Python's shelve module
    # to make a persistent dict.
    if not os.access(settings.SHELVED_ANNOTATIONS_DIR, os.R_OK | os.W_OK):
        # Don't catch this error and display it to the user.
        # Just let it become a server error to be e-mailed to the admins.
        raise DirectoryAccessError(
            "The SHELVED_ANNOTATIONS_DIR either does not exist, is not readable, or is not writable. Please rectify this."
        )
    annotation_dict_id = rand_string(10)
    annotation_dict = shelve.open(os.path.join(
        settings.SHELVED_ANNOTATIONS_DIR,
        'source{source_id}_{dict_id}'.format(
            source_id=source.id,
            dict_id=annotation_dict_id,
        ),
    ))

    for line_num, line in enumerate(annoFile, 1):

        stripped_line = line.strip()

        # Ignore empty lines.
        if stripped_line == '':
            continue

        # Split the line into words/tokens.
        unstripped_words = stripped_line.split(';')
        # Strip leading and trailing whitespace from each token.
        words = [w.strip() for w in unstripped_words]

        # Check that all expected words/tokens are there.
        is_valid_format_with_label = (len(words) == num_words_with_label)
        is_valid_format_without_label = (len(words) == num_words_without_label)
        words_format_is_valid = (
            (expecting_labels and is_valid_format_with_label)
            or (not expecting_labels and (is_valid_format_with_label or is_valid_format_without_label))
        )
        if expecting_labels:
            num_words_expected = num_words_with_label
        else:
            num_words_expected = num_words_without_label

        if not words_format_is_valid:
            annotation_dict.close()
            annoFile.close()
            raise FileContentError(file_error_format_str.format(
                line_num=line_num,
                line=stripped_line,
                error=str_consts.ANNOTATION_FILE_TOKEN_COUNT_ERROR_FMTSTR.format(
                    num_words_expected=num_words_expected,
                    num_words_found=len(words),
                )
            ))

        # Encode the line data into a dictionary: {'value1':'Shore2', 'row':'575', ...}
        if is_valid_format_with_label:
            lineData = dict(zip(words_format_with_label, words))
        else:  # valid format without label
            lineData = dict(zip(words_format_without_label, words))

        try:
            row = int(lineData['row'])
            if row <= 0:
                raise ValueError
        except ValueError:
            annotation_dict.close()
            annoFile.close()
            raise FileContentError(file_error_format_str.format(
                line_num=line_num,
                line=stripped_line,
                error=str_consts.ANNOTATION_FILE_ROW_NOT_POSITIVE_INT_ERROR_FMTSTR.format(row=lineData['row']),
            ))

        try:
            col = int(lineData['col'])
            if col <= 0:
                raise ValueError
        except ValueError:
            annotation_dict.close()
            annoFile.close()
            raise FileContentError(file_error_format_str.format(
                line_num=line_num,
                line=stripped_line,
                error=str_consts.ANNOTATION_FILE_COL_NOT_POSITIVE_INT_ERROR_FMTSTR.format(column=lineData['col']),
            ))

        if expecting_labels:
            # Check that the label code corresponds to a label in the database
            # and in the source's labelset.
            # Only check this if the label code hasn't been seen before
            # in the annotations file.

            label_code = lineData['label']
            if label_code not in uniqueLabelCodes:

                labelObjs = Label.objects.filter(code=label_code)
                if len(labelObjs) == 0:
                    annotation_dict.close()
                    annoFile.close()
                    raise FileContentError(file_error_format_str.format(
                        line_num=line_num,
                        line=stripped_line,
                        error=str_consts.ANNOTATION_FILE_LABEL_NOT_IN_DATABASE_ERROR_FMTSTR.format(label_code=label_code),
                    ))

                labelObj = labelObjs[0]
                if labelObj not in source.labelset.labels.all():
                    annotation_dict.close()
                    annoFile.close()
                    raise FileContentError(file_error_format_str.format(
                        line_num=line_num,
                        line=stripped_line,
                        error=str_consts.ANNOTATION_FILE_LABEL_NOT_IN_LABELSET_ERROR_FMTSTR.format(label_code=label_code),
                    ))

                uniqueLabelCodes.append(label_code)

        # Get and check the photo year to make sure it's valid.
        # We'll assume the year is the first 4 characters of the date.
        year = lineData['date'][:4]
        try:
            datetime.date(int(year),1,1)
        # Year is non-coercable to int, or year is out of range (e.g. 0 or negative)
        except ValueError:
            annotation_dict.close()
            annoFile.close()
            raise FileContentError(file_error_format_str.format(
                line_num=line_num,
                line=stripped_line,
                error=str_consts.ANNOTATION_FILE_YEAR_ERROR_FMTSTR.format(year=year),
            ))

        # TODO: Check if the row and col in this line are a valid row and col
        # for the image.  Need the image to do that, though...


        # Use the location values and the year to build a string identifier for the image, such as:
        # Shore1;Reef5;...;2008
        valueList = [lineData['value'+str(i)] for i in range(1,numOfKeys+1)]
        imageIdentifier = get_image_identifier(valueList, year)

        # Add/update a dictionary entry for the image with this identifier.
        # The dict entry's value is a list of labels.  Each label is a dict:
        # {'row':'484', 'col':'320', 'label':'POR'}
        if not annotation_dict.has_key(imageIdentifier):
            annotation_dict[imageIdentifier] = []

        # Append the annotation as a dict containing row, col, and label
        # (or just row and col, if no labels).
        #
        # Can't append directly to annotation_dict[imageIdentifier], due to
        # how shelved dicts work. So we use this pattern with a temporary
        # variable.
        # See http://docs.python.org/library/shelve.html?highlight=shelve#example
        tmp_data = annotation_dict[imageIdentifier]
        if expecting_labels:
            tmp_data.append(
                dict(row=row, col=col, label=lineData['label'])
            )
        else:
            tmp_data.append(
                dict(row=row, col=col)
            )
        annotation_dict[imageIdentifier] = tmp_data

    annoFile.close()

    return (annotation_dict, annotation_dict_id)


def image_upload_process(imageFile, imageOptionsForm,
                         is_uploading_points_or_annotations,
                         annotation_dict_id,
                         annotation_options_form,
                         source, currentUser):

    dupeOption = imageOptionsForm.cleaned_data['skip_or_replace_duplicates']

    filename = imageFile.name
    is_dupe = False
    metadata_dict = None
    metadata_obj = Metadata(height_in_cm=source.image_height_in_cm)

    if imageOptionsForm.cleaned_data['specify_metadata'] == 'filenames':

        filename_check_result = check_image_filename(filename, source)
        filename_status = filename_check_result['status']

        if filename_status == 'error':
            # This case should never happen if the pre-upload
            # status checking is doing its job, but just in case...
            return dict(
                status=filename_status,
                message=u"{m}".format(m=filename_check_result['message']),
                link=None,
                title=None,
            )

        elif filename_status == 'dupe':
            is_dupe = True
            dupe_image = filename_check_result['dupe']

            if dupeOption == 'skip':
                # This case should never happen if the pre-upload
                # status checking is doing its job, but just in case...
                return dict(
                    status='error',
                    message="Skipped (duplicate found)",
                    link=reverse('image_detail', args=[dupe_image.id]),
                    title=dupe_image.get_image_element_title(),
                )
            elif dupeOption == 'replace':
                # Delete the dupe, and proceed with uploading this file.
                dupe_image.delete()

        # Set the metadata
        metadata_dict = filename_check_result['metadata_dict']

        value_dict = get_location_value_objs(source, metadata_dict['values'], createNewValues=True)
        photo_date = datetime.date(
            year = int(metadata_dict['year']),
            month = int(metadata_dict['month']),
            day = int(metadata_dict['day'])
        )

        metadata_obj.name = metadata_dict['name']
        metadata_obj.photo_date = photo_date
        for key, value in value_dict.iteritems():
            setattr(metadata_obj, key, value)
    else:
        # Not specifying data from filenames.
        # *** Unused case for now ***
        metadata_obj.name = filename
        is_dupe = False

    # Use the location values and the year to build a string identifier for the image, such as:
    # Shore1;Reef5;...;2008
    # Convert to a string (instead of a unicode string) for the shelve key lookup.
    image_identifier = str(get_image_identifier(metadata_dict['values'], metadata_dict['year']))

    image_annotations = None
    has_points_or_annotations = False
    if is_uploading_points_or_annotations:
        annotation_dict = shelve.open(os.path.join(
            settings.SHELVED_ANNOTATIONS_DIR,
            'source{source_id}_{dict_id}'.format(
                source_id=source.id,
                dict_id=annotation_dict_id,
            ),
        ))
        if annotation_dict.has_key(image_identifier):
            image_annotations = annotation_dict[image_identifier]
            has_points_or_annotations = True
        annotation_dict.close()

    if has_points_or_annotations:
        # Image upload with points/annotations

        is_uploading_annotations_not_just_points = annotation_options_form.cleaned_data['is_uploading_annotations_not_just_points']
        imported_user = get_imported_user()

        status = ImageStatus()
        status.save()

        metadata_obj.annotation_area = AnnotationAreaUtils.IMPORTED_STR
        metadata_obj.save()

        img = Image(
            original_file=imageFile,
            uploaded_by=currentUser,
            point_generation_method=PointGen.args_to_db_format(
                point_generation_type=PointGen.Types.IMPORTED,
                imported_number_of_points=len(image_annotations)
            ),
            metadata=metadata_obj,
            source=source,
            status=status,
        )
        img.save()

        # Iterate over this image's annotations and save them.
        point_num = 0
        for anno in image_annotations:

            # Save the Point in the database.
            point_num += 1
            point = Point(row=anno['row'], column=anno['col'], point_number=point_num, image=img)
            point.save()

            if is_uploading_annotations_not_just_points:
                label = Label.objects.filter(code=anno['label'])[0]

                # Save the Annotation in the database, marking the annotations as imported.
                annotation = Annotation(user=imported_user,
                    point=point, image=img, label=label, source=source)
                annotation.save()

        img.status.hasRandomPoints = True
        if is_uploading_annotations_not_just_points:
            img.status.annotatedByHuman = True
        img.status.save()
    else:
        # Image upload, no points/annotations
        image_status = ImageStatus()
        image_status.save()

        metadata_obj.annotation_area = source.image_annotation_area
        metadata_obj.save()

        # Save the image into the DB
        img = Image(original_file=imageFile,
            uploaded_by=currentUser,
            point_generation_method=source.default_point_generation_method,
            metadata=metadata_obj,
            source=source,
            status=image_status,
        )
        img.save()

        # Generate and save points
        generate_points(img)

    if is_dupe:
        success_message = "Uploaded (replaced duplicate)"
    else:
        success_message = "Uploaded"

    return dict(
        status='ok',
        message=success_message,
        link=reverse('image_detail', args=[img.id]),
        title=img.get_image_element_title(),
        image_id=img.id,
    )


def find_dupe_image(source, values=None, year=None, **kwargs):
    """
    Sees if the given source already has an image with the given arguments.

    :param source: The source to check.
    :param values: The image's location values as a list of strings.
    :param year: The image's photo-date year.
    :param kwargs: This is just to accept other arguments that might've come
        with an unpacked metadata dict (the typical input for this function),
        although we won't be using these other arguments.
    :returns: If a duplicate image was found, returns that duplicate.  If no
        duplicate was found, returns None.
    """

    # Get Value objects of the value names given in "values".
    try:
        valueObjDict = get_location_value_objs(source, values, createNewValues=False)
    except ValueObjectNotFoundError:
        # One or more of the values weren't found in the DB.
        # So this image surely doesn't have a dupe in the DB.
        return None

    # Get all the metadata objects in the DB with these location values and year.
    #
    # Note: if 0 location keys is possible at all, this will get metadata from
    # other sources.  We'll filter by source in the next step, though.
    metaMatches = Metadata.objects.filter(photo_date__year=year, **valueObjDict)

    # Get the images from our source that have this metadata.
    imageMatches = Image.objects.filter(source=source, metadata__in=metaMatches)

    if len(imageMatches) >= 1:
        return imageMatches[0]
    else:
        return None


def filename_to_metadata(filename, source):
    """
    Takes an image filename without the extension.

    Returns a dict of the location values, and the photo year, month, and day.
    {'values': ['Shore3', 'Reef 5', 'Loc10'],
     'year': 2007, 'month': 8, 'day': 15}
    """

    metadataDict = dict()

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
        raise FilenameError(str_consts.FILENAME_PARSE_ERROR_STR)

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
        # Too few or too many dash-separated tokens.
        # Note that this may or may not be something that the user intended
        # as a date.  An appropriately flexible error message is needed.
        raise FilenameError(str_consts.FILENAME_DATE_PARSE_ERROR_FMTSTR.format(date_token=dateToken))
    # YYYYMMDD parsing:
#    if len(dateToken) != 8:
#        raise dateFormatError
#    year, month, day = dateToken[:4], dateToken[4:6], dateToken[6:8]

    try:
        datetime.date(int(year), int(month), int(day))
    except ValueError:
        # Either non-integer date params, or date params are
        # out of valid range (e.g. month 13).
        raise FilenameError(str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token=dateToken))

    # Make the values into a tuple, so the metadata can potentially be
    # hashed and used in lookups.
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


def metadata_dict_to_string_list(metadata_dict):
    return metadata_dict['values'] + [metadata_dict['year']]


def metadata_dict_to_dupe_comparison_key(metadata_dict):
    # TODO: Be tolerant of semicolons in metadata.
    return ';'.join(metadata_dict_to_string_list(metadata_dict))


def metadata_dupe_comparison_key_to_display(metadata_key):
    """
    metadata_key is a result of metadata_dict_to_dupe_comparison_key().
    This function turns the key into a displayable string.
    """
    return metadata_key.replace(';', ' ')


def check_image_filename(filename, source):
    """
    When gathering uploaded-image metadata from filenames, this function
    checks the filename and determines whether the file:
    - Has a filename error
    - Is a duplicate of an existing image
    - Neither
    """
    try:
        metadata_dict = filename_to_metadata(filename, source)
    except FilenameError as error:
        # Filename parse error.
        return dict(
            status='error',
            message=error.message,
        )

    dupe = find_dupe_image(source, **metadata_dict)
    if dupe:
        return dict(
            status='dupe',
            metadata_dict=metadata_dict,
            dupe=dupe,
        )
    else:
        return dict(
            status='ok',
            metadata_dict=metadata_dict,
        )


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