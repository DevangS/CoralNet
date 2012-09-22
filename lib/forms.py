from django import forms

class ContactForm(forms.Form):
    """
    Allows a user to send a general email to the site admins.
    """
    subject = forms.CharField(
        label='Subject',
        # Total length of the subject (including any auto-added prefix)
        # should try not to exceed 78 characters.
        max_length=55,
    )
    message = forms.CharField(
        label='Message',
        max_length=5000,
        widget=forms.Textarea(
            attrs={'class': 'large'},
        ),
    )