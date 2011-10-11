from dajaxice.decorators import dajaxice_register
from django.utils import simplejson

@dajaxice_register
def ajax_save_annotations(request, annotations):
    """
    Called via Ajax from the annotation tool form, if the user clicked
    the "Save Annotations" button.

    Takes:
    Returns: nothing
    """

    pass
