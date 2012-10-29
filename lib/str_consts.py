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

ANNOTATION_FILE_FULL_ERROR_MESSAGE_FMTSTR = _(u"On line {line_num}:\n{line}\n{error}")
ANNOTATION_FILE_TOKEN_COUNT_ERROR_FMTSTR = _(u"We expected {num_words_expected} semicolon-separated tokens, but found {num_words_found} instead.")
ANNOTATION_FILE_ROW_NOT_POSITIVE_INT_ERROR_FMTSTR = _(u"{row} is not a valid row (not a positive integer number).")
ANNOTATION_FILE_COL_NOT_POSITIVE_INT_ERROR_FMTSTR = _(u"{column} is not a valid column (not a positive integer number).")
ANNOTATION_FILE_LABEL_NOT_IN_DATABASE_ERROR_FMTSTR = _(u"This line has label code {label_code}, but CoralNet has no label with this code.")
ANNOTATION_FILE_LABEL_NOT_IN_LABELSET_ERROR_FMTSTR = _(u"This line has label code {label_code}, but your labelset has no label with this code.")
ANNOTATION_FILE_YEAR_ERROR_FMTSTR = _(u"{year} is not a valid year.")

UPLOAD_ANNOTATIONS_ON_AND_NO_ANNOTATION_DICT_ERROR_STR = _(u"Could not find annotation data")