from django import forms
from images.models import Image


class ContactForm(forms.Form):
    """
    Allows a user to send a general email to the site admins.
    """
    email = forms.EmailField(
        label='Your email address',
        help_text="Enter your email address so we can reply to you.",
    )
    subject = forms.CharField(
        label='Subject',
        # Total length of the subject (including any auto-added prefix)
        # should try not to exceed 78 characters.
        # http://stackoverflow.com/questions/1592291/
        max_length=55,
    )
    message = forms.CharField(
        label='Message/Body',
        max_length=5000,
        widget=forms.Textarea(
            attrs={'class': 'large'},
        ),
    )

    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        if user.is_authenticated():
            del self.fields['email']



def clean_comma_separated_image_ids_field(value, source):
    """
    Clean a char field that contains some image ids separated by commas.
    e.g. "5,6,8,9"

    This would preferably go in a custom Field class's clean() method,
    but I don't know how to define a custom Field's clean() method that
    takes a custom parameter (in this case, the source). -Stephen
    """
    # Turn the comma-separated string of ids into a proper list.
    id_str_list = value.split(',')
    id_list = []

    for img_id in id_str_list:
        try:
            id_num = int(img_id)
        except ValueError:
            # for whatever reason, the img_id str can't be interpreted
            # as int.  just skip this faulty id.
            continue

        # Check that these ids correspond to images in the source (not to
        # images of other sources).
        # This ensures that any attempt to forge POST data to specify
        # other sources' image ids will not work.
        try:
            Image.objects.get(pk=id_num, source=source)
        except Image.DoesNotExist:
            # the image either doesn't exist or isn't in this source.
            # skip it.
            #raise ValueError("no: %d".format(id_num))
            continue

        id_list.append(id_num)

    return id_list
    