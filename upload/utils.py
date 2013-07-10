import datetime
import os
import csv
from os.path import splitext
import shelve

from django.conf import settings
from django.core.urlresolvers import reverse
#from BeautifulSoup import UnicodeDammit

from accounts.utils import get_imported_user
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import Label, Annotation
from images.model_utils import PointGen
from images.models import Metadata, ImageStatus, Image, Point, Source
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

def store_csv_file(csv_file, source):
    """
    This will store the csv_file uploaded using python's shelve module temporarily.
    Also does a few error checks, such as if the length of the rows are too long,
    if there are duplicate filenames present in the file, etc.
    """

    # The annotation dict needs to be kept on disk temporarily until all the
    # Ajax upload requests are done. Thus, we'll use Python's shelve module
    # to make a persistent dict.
    if not os.access(settings.SHELVED_ANNOTATIONS_DIR, os.R_OK | os.W_OK):
        # Don't catch this error and display it to the user.
        # Just let it become a server error to be e-mailed to the admins.
        raise DirectoryAccessError(
            "The SHELVED_ANNOTATIONS_DIR either does not exist, is not readable, or is not writable. Please rectify this."
        )
    csv_dict_id = rand_string(10)
    csv_dict = shelve.open(os.path.join(
        settings.SHELVED_ANNOTATIONS_DIR,
        'csv_source{source_id}_{dict_id}.db'.format(
            source_id=source.id,
            dict_id=csv_dict_id,
        ),
    ))

    # TODO: Fix this so it works with various charsets

#    csv_file_to_unicode_string = UnicodeDammit(csv_file.read()).unicode
#    csv_file_converted = csv_file_to_unicode_string.splitlines()

#    reader = csv.reader(csv_file_converted, dialect='excel')
    reader = csv.reader(csv_file, dialect='excel')
    num_keys = source.num_of_keys()
    filenames_processed = []

    for row in reader:
        metadata_for_file = {}

        # Gets filename, checks if we already found data for this filename.
        filename = row.pop(0)
        if filename in filenames_processed:
            csv_dict.close()
            raise FileContentError('metadata for file "{file}" found twice in CSV file.'.format(
                file=filename,
            ))
        else:
            filenames_processed.append(filename)

            valueList = []
            date = ""
            # Now loop through that row and gather metadata from the file.
            for i, element in enumerate(row):
                if (i == 0):
                    date = element
                elif (i == 1):
                    valueList.append(element)
                elif (i == 2):
                    if (num_keys < 2):
                        continue
                    valueList.append(element)
                elif (i == 3):
                    if (num_keys < 3):
                        continue
                    valueList.append(element)
                elif (i == 4):
                    if (num_keys < 4):
                        continue
                    valueList.append(element)
                elif (i == 5):
                    if (num_keys < 5):
                        continue
                    valueList.append(element)
                elif (i == 6):
                    metadata_for_file['height'] = element
                elif (i == 7):
                    metadata_for_file['latitude'] = element
                elif (i == 8):
                    metadata_for_file['longitude'] = element
                elif (i == 9):
                    metadata_for_file['depth'] = element
                elif (i == 10):
                    metadata_for_file['camera'] = element
                elif (i == 11):
                    metadata_for_file['photographer'] = element
                elif (i == 12):
                    metadata_for_file['water_quality'] = element
                elif (i == 13):
                    metadata_for_file['strobes'] = element
                elif (i == 14):
                    metadata_for_file['framing_gear'] = element
                elif (i == 15):
                    metadata_for_file['white_balance'] = element
                else:
                    csv_dict.close()
                    raise FileContentError('CSV file contains too many values for line specifying metadata for {file}.'.format(
                        file=filename,
                    ))

            try:
                year, month, day = date.split("-")
            except ValueError:
                # Too few or too many dash-separated tokens.
                # Note that this may or may not be something that the user intended
                # as a date.  An appropriately flexible error message is needed.
                csv_dict.close()
                raise FileContentError(str_consts.DATE_PARSE_ERROR_FMTSTR.format(date_token=date))
            # YYYYMMDD parsing:
            #    if len(dateToken) != 8:
            #        raise dateFormatError
            #    year, month, day = dateToken[:4], dateToken[4:6], dateToken[6:8]
            try:
                datetime.date(int(year), int(month), int(day))
            except ValueError:
                # Either non-integer date params, or date params are
                # out of valid range (e.g. month 13).
                csv_dict.close()
                raise FilenameError(str_consts.DATE_VALUE_ERROR_FMTSTR.format(date_token=date))

            metadata_for_file['day'] = day
            metadata_for_file['month'] = month
            metadata_for_file['year'] = year
            metadata_for_file['values'] = valueList
        csv_dict[filename] = metadata_for_file

    return (csv_dict, csv_dict_id)

def filename_to_metadata_in_csv(filename, source, csv_dict_id):
    """
    This will take the csv_dict_id, the source, and a filename, and attempt to match the filename with metadata.
    If it does find a match, a dictionary of the file will be returned. If not, an error will be thrown.
    """

    # these errors should not happen, but good to check anyway
    if not csv_dict_id:
        return dict(
            status='error',
            message=u"{m}".format(m="CSV file was not uploaded."),
            link=None,
            title=None,
        )

    csv_dict_filename = os.path.join(
        settings.SHELVED_ANNOTATIONS_DIR,
        'csv_source{source_id}_{dict_id}.db'.format(
            source_id=source.id,
            dict_id=csv_dict_id,
        ),
    )

    if not os.path.isfile(csv_dict_filename):
        return dict(
            status='error',
            message="CSV file could not be found.",
            link=None,
            title=None,
        )

    csv_dict = shelve.open(csv_dict_filename)


    try:
        #index into the csv_dict with the filename. the str() is to handle
        #the case where the filename is a unicode object instead of a str;
        #unicode objects can't index into dicts.
        metadata = csv_dict[str(filename)]
        #if filename in the dict, then return the dict containing metadata
        return dict(
            status="ok",
            metadata_dict=metadata
        )
    except KeyError:
        #if filename is not in the dict, we return an error message.
        return dict(
            status='error',
            message="Does not have any metadata specified in CSV file.",
            link=None,
            title=None,
        )

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
                         annotation_dict_id,
                         csv_dict_id,
                         annotation_options_form,
                         source, currentUser):

    is_uploading_points_or_annotations = annotation_options_form.cleaned_data['is_uploading_points_or_annotations']

    filename = imageFile.name
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

    elif imageOptionsForm.cleaned_data['specify_metadata'] == 'csv':

        if not csv_dict_id:
            return dict(
                status='error',
                message=u"{m}".format(m="CSV file was not uploaded."),
                link=None,
                title=None,
            )

        csv_dict_filename = os.path.join(
            settings.SHELVED_ANNOTATIONS_DIR,
            'csv_source{source_id}_{dict_id}.db'.format(
                source_id=source.id,
                dict_id=csv_dict_id,
            ),
        )

        # Corner case: the specified shelved annotation file doesn't exist.
        # Perhaps the file was created a while ago and has been pruned since,
        # or perhaps there is a bug.
        if not os.path.isfile(csv_dict_filename):
            return dict(
                status='error',
                message="CSV file could not be found - if you provided the .csv file a while ago, maybe it just timed out. Please retry the upload.",
                link=None,
                title=None,
            )

        csv_dict = shelve.open(csv_dict_filename)

        #index into the csv_dict with the filename. the str() is to handle
        #the case where the filename is a unicode object instead of a str;
        #unicode objects can't index into dicts.
        metadata_dict = csv_dict[str(filename)]

        csv_dict.close()

        value_dict = get_location_value_objs(source, metadata_dict['values'], createNewValues=True)
        photo_date = datetime.date(
            year = int(metadata_dict['year']),
            month = int(metadata_dict['month']),
            day = int(metadata_dict['day'])
        )

        metadata_obj.name = filename
        if photo_date:
            metadata_obj.photo_date = photo_date
        if 'latitude' in metadata_dict:
            metadata_obj.latitude = metadata_dict['latitude']
        if 'height' in metadata_dict:
            metadata_obj.height_in_cm = metadata_dict['height']
        if 'longitude' in metadata_dict:
            metadata_obj.longitude = metadata_dict['longitude']
        if 'depth' in metadata_dict:
            metadata_obj.depth = metadata_dict['depth']
        if 'camera' in metadata_dict:
            metadata_obj.camera = metadata_dict['camera']
        if 'photographer' in metadata_dict:
            metadata_obj.photographer = metadata_dict['photographer']
        if 'water_quality' in metadata_dict:
            metadata_obj.water_quality = metadata_dict['water_quality']
        if 'strobes' in metadata_dict:
            metadata_obj.strobes = metadata_dict['strobes']
        if 'framing_gear' in metadata_dict:
            metadata_obj.framing = metadata_dict['framing_gear']
        if 'white_balance' in metadata_dict:
            metadata_obj.balance = metadata_dict['white_balance']
        for key, value in value_dict.iteritems():
            setattr(metadata_obj, key, value)

    else:

        # Not specifying any metadata at upload time.
        metadata_obj.name = filename


    image_annotations = None
    has_points_or_annotations = False

    if is_uploading_points_or_annotations:

        # Corner case: somehow, we're uploading with points+annotations and without
        # a checked annotation file specified.  This probably indicates a bug.
        if not annotation_dict_id:
            return dict(
                status='error',
                message=u"{m}".format(m=str_consts.UPLOAD_ANNOTATIONS_ON_AND_NO_ANNOTATION_DICT_ERROR_STR),
                link=None,
                title=None,
            )

        annotation_dict_filename = os.path.join(
            settings.SHELVED_ANNOTATIONS_DIR,
            'source{source_id}_{dict_id}'.format(
                source_id=source.id,
                dict_id=annotation_dict_id,
            ),
        )

        # Corner case: the specified shelved annotation file doesn't exist.
        # Perhaps the file was created a while ago and has been pruned since,
        # or perhaps there is a bug.
        if not os.path.isfile(annotation_dict_filename):
            return dict(
                status='error',
                message="Annotations could not be found - if you provided the .txt file a while ago, maybe it just timed out. Please retry the upload.",
                link=None,
                title=None,
            )


        # Use the location values and the year to build a string identifier for the image, such as:
        # Shore1;Reef5;...;2008
        # Convert to a string (instead of a unicode string) for the shelve key lookup.
        image_identifier = str(get_image_identifier(metadata_dict['values'], metadata_dict['year']))

        annotation_dict = shelve.open(annotation_dict_filename)

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

    success_message = "Uploaded"

    return dict(
        status='ok',
        message=success_message,
        link=reverse('image_detail', args=[img.id]),
        title=img.get_image_element_title(),
        image_id=img.id,
    )


def find_dupe_image(source, image_name):
    """
    Sees if the given source already has an image with the given arguments.

    :param source: The source to check.
    :param image_name: The image's name; based on its filename.
    :returns: If a duplicate image was found, returns that duplicate.  If no
        duplicate was found, returns None.
    """
    imageMatches = Image.objects.filter(source=source, metadata__name=image_name)

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
        raise FilenameError(str_consts.DATE_PARSE_ERROR_FMTSTR.format(date_token=dateToken))
    # YYYYMMDD parsing:
#    if len(dateToken) != 8:
#        raise dateFormatError
#    year, month, day = dateToken[:4], dateToken[4:6], dateToken[6:8]

    try:
        datetime.date(int(year), int(month), int(day))
    except ValueError:
        # Either non-integer date params, or date params are
        # out of valid range (e.g. month 13).
        raise FilenameError(str_consts.DATE_VALUE_ERROR_FMTSTR.format(date_token=dateToken))

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


def check_image_filename(filename, source, verify_metadata=True):
    """
    When gathering uploaded-image metadata from filenames, this function
    checks the filename and determines whether the file:
    - Has a filename error
    - Is a duplicate of an existing image
    - Neither
    """
    metadata_dict = None

    if verify_metadata:
        try:
            metadata_dict = filename_to_metadata(filename, source)
        except FilenameError as error:
            # Filename parse error.
            return dict(
                status='error',
                message=error.message,
            )
        image_name = metadata_dict['name']
    else:
        image_name = filename

    dupe = find_dupe_image(source, image_name)

    return_dict = dict()

    if dupe:
        return_dict['status'] = 'possible_dupe'
        return_dict['dupe'] = dupe
    else:
        return_dict['status'] = 'ok'

    if metadata_dict:
        return_dict['metadata_dict'] = metadata_dict

    return return_dict
