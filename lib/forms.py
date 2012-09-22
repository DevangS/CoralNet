from django import forms

class ContactForm(forms.Form):
    """
    Allows a user to send a general email to the site admins.
    """
    subject = forms.CharField(
        label='Subject',
        max_length=100,  # TODO: What's a good character limit?
    )
    message = forms.CharField(
        label='Message',
        max_length=5000,  # TODO: What's a good character limit?
        widget=forms.Textarea(
            attrs={'class': 'large'},
        ),
    )