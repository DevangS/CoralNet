from django.core.urlresolvers import reverse
from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from images.models import Source
from images.utils import filename_to_metadata, find_dupe_image

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

        try:
            fileMetadata = filename_to_metadata(filename, source)
        except ValueError:
            # Failed to parse the filename for metadata
            statusList.append({'status': 'Filename error'})

        else:
            if checkDupes:
                dupeImage = find_dupe_image(source, **fileMetadata)
                if dupeImage:
                    statusList.append({'status': 'Duplicate found',
                                       'url': reverse('image_detail', args=[dupeImage.id])
                    })
                else:
                    statusList.append({'status': 'Ready'})

    # return a dictionary to the JS callback
    return simplejson.dumps({
        'statusList': statusList,
    })
