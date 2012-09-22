# Messages that can be displayed at the top of a page.
#
# Constants don't really need to be used for one-time messages,
# just messages that can appear in multiple situations.
from django.utils.translation import ugettext_lazy as _

CONTACT_EMAIL_SENT = _(u"Your email was sent to the admins!")
FORM_ERRORS = _(u"Please correct the errors below.")