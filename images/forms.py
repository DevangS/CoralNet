from django.forms import ModelForm
from images.models import Source

class ImageSourceForm(ModelForm):
    class Meta:
        model = Source

    #error_css_class = ...
    #required_css_class = ...
    