import datetime
from images.models import Value1, Value2, Value3, Value4, Value5, Image, Metadata

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


def get_location_value_str_list(image):
    """
    Takes an Image object.
    Returns its location values as a list of strings:
    ['Shore3', 'Reef 5', 'Loc10']
    """

    valueList = []
    metadata = image.metadata

    for valueIndex, valueClass in [
            ('value1', Value1),
            ('value2', Value2),
            ('value3', Value3),
            ('value4', Value4),
            ('value5', Value5)
    ]:
        valueObj = getattr(metadata, valueIndex)
        if valueObj:
            valueList.append(valueObj.name)
        else:
            break

    return valueList


def filename_to_metadata(filenameWithoutExt, source):
    """
    Takes the filename without the extension.

    Returns a dict of the location values, and the photo year, month, and day.
    {'values': ['Shore3', 'Reef 5', 'Loc10'],
     'year': 2007, 'month': 8, 'day': 15}
    """

    metadataDict = dict()

    parseError = ValueError('Could not properly extract metadata from the filename "%s".' % filenameWithoutExt)
    dateError = ValueError('Invalid date format or values.')
    numOfKeys = source.num_of_keys()

    # value1_value2_..._YYYY-MM-DD
    tokensFormat = ['value'+str(i) for i in range(1, numOfKeys+1)]
    tokensFormat += ['date']
    numTokensExpected = len(tokensFormat)

    # Make a list of the metadata 'tokens' from the filename
    tokens = filenameWithoutExt.split('_')
    if len(tokens) != numTokensExpected:
        raise parseError

    # Encode the filename data into a dictionary: {'value1':'Shore2', 'date':'2008-12-18', ...}
    filenameData = dict(zip(tokensFormat, tokens))

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
