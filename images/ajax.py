from django.core.urlresolvers import reverse
from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from images.models import Source
from images.utils import check_image_filename

@dajaxice_register
def ajax_assess_file_status(request, filenames, sourceId, checkDupes):
    """
    Called via Ajax from the image upload form, if the user checked
    "has keys from filenames" in the upload form.

    Takes a list of filenames from the image upload form, and returns:
    - List containing the status of each file
    - Number of duplicates, if that was asked for
    """

    # TODO: Check if any two files in the request are duplicates of
    # each other; don't just compare against the images on the server.

    statusList = []

    source = Source.objects.get(id=sourceId)

    for filename in filenames:

        result = check_image_filename(filename, source)
        status = result['status']

        if status == 'error' or status == 'ok':
            statusList.append(dict(
                status=status,
            ))
        elif status == 'dupe':
            dupe_image = result['dupe']
            statusList.append(dict(
                status=status,
                url=reverse('image_detail', args=[dupe_image.id]),
                title=dupe_image.get_image_element_title(),
            ))

    # return a dictionary to the JS callback
    return simplejson.dumps({
        'statusList': statusList,
    })
