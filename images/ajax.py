from django.core.urlresolvers import reverse
from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from os.path import splitext
from images.models import Source
from images.models import find_dupe_image
from images.utils import filename_to_metadata

@dajaxice_register
def ajax_assess_file_status(request, filenames, sourceId, checkDupes):
    """
    Called via Ajax from the image upload form, if the user checked
    "has keys from filenames" in the upload form.

    Takes a list of filenames from the image upload form, and returns:
    - List containing the status of each file
    - Number of duplicates, if that was asked for
    """

    statusList = []

    source = Source.objects.get(id=sourceId)

    for filename in filenames:
        filenameWithoutExt = splitext(filename)[0]

        try:
            fileMetadata = filename_to_metadata(filenameWithoutExt, source)
        except ValueError:
            # Failed to parse the filename for metadata
            statusList.append({'status': 'Filename error'})

        else:
            if checkDupes:
                dupeImage = find_dupe_image(source, **fileMetadata)
                if dupeImage:
                    statusList.append({'status': 'Duplicate found',
                                       'url': reverse('image_detail', args=[sourceId, dupeImage.id])
                    })
                else:
                    statusList.append({'status': 'Ready'})

    # return a dictionary to the JS callback
    return simplejson.dumps({
        'statusList': statusList,
    })
