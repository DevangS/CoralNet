# General utility functions can go here.

import os
import random
import string

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
    #TODO: Use the directory argument to check for filename collisions with existing files

    extension = os.path.splitext(originalFilename)[1]
    filenameBase = rand_string(numOfChars)
    return os.path.join(directory, filenameBase + extension)
