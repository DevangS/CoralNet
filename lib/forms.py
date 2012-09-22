from django.forms import Form
from django.forms.fields import CharField
from django.forms.widgets import Textarea

class ContactForm(Form):
    """
    Allows a user to send a general email to the site admins.
    """

    subject = CharField(
        label='Subject',
        max_length=255,  # TODO: What's a good character limit?
    )
    message = CharField(
        label='Message',
        max_length=5000,  # TODO: What's a good character limit?
        widget=Textarea(),
    )