# String constants.
# Other than top-of-page messages; those are found in msg_consts.py.
from django.utils.translation import ugettext_lazy as _

CONTACT_EMAIL_SUBJECT_FMTSTR = _(u"Contact Us - {username} - {base_subject}")
CONTACT_EMAIL_MESSAGE_FMTSTR = _(u"This email was sent using the Contact Us form.\n"
                                 u"\n"
                                 u"Username: {username}\n"
                                 u"User's email: {user_email}\n"
                                 u"\n"
                                 u"{base_message}")

FILENAME_DATE_PARSE_ERROR_FMTSTR = _(u"Tried to parse {date_token} as a date, but failed")
FILENAME_DATE_VALUE_ERROR_FMTSTR = _(u"Could not recognize {date_token} as a valid year-month-day combination")
FILENAME_PARSE_ERROR_STR = _(u"Could not extract metadata from filename")

UPLOAD_PREVIEW_SAME_METADATA_ERROR_FMTSTR = _(u"Multiple images with same metadata: {metadata}")