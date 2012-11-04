# General utility functions can go here.

import os
import random
import string
from django.utils import functional
from django.utils.http import urlencode

def rand_string(numOfChars):
    """
    Generates a string of lowercase letters and numbers.
    That makes 36^10 = 3 x 10^15 possibilities.

    If we generate filenames randomly, it's harder for people to guess filenames
    and type in their URLs directly to bypass permissions.
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(numOfChars))

def generate_random_filename(directory, originalFilename, numOfChars):
    """
    Generate a random filename for a file upload.  The filename will
    have numOfChars random characters.  Also prepends the directory
    argument to get a filepath which is only missing the MEDIA_ROOT
    part at the beginning.

    The return value can be used as an upload_to argument for a FileField
    ImageField, ThumbnailerImageField, etc.  An upload_to argument is
    automatically prepended with MEDIA_ROOT to get the upload filepath.
    """
    # TODO: Use the directory argument to check for filename collisions with existing files.
    # To unit test this, use a Mocker or similar on the filename randomizer
    # to make filename collisions far more likely.

    extension = os.path.splitext(originalFilename)[1]
    filenameBase = rand_string(numOfChars)
    return os.path.join(directory, filenameBase + extension)

def url_with_querystring(path, **kwargs):
    """
    Takes a base URL (path) and GET query arguments (kwargs).
    Returns the complete GET URL.

    NOTE:
    Any kwargs with special characters like '/' and ' ' will be
    escaped with %2f, %20, etc.

    Source:
    http://stackoverflow.com/a/5341769/859858
    """
    return path + '?' + urlencode(kwargs)

def is_django_str(s):
    """
    Checks that the argument is either:
    (a) an instance of basestring, or
    (b) a Django lazy-translation string.

    :param s: Object to check the type of.
    :return: True if s is a Django string, False otherwise.
    """
    if isinstance(s, basestring):
        return True
    elif isinstance(s, functional.Promise):
        return True
    else:
        return False
