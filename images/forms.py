from django.forms import ModelForm, TextInput
from images.models import Source
from CoralNet.forms import FormHelper

class ImageSourceForm(ModelForm):
    class Meta:
        model = Source
        widgets = {
            'key1': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key2': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key3': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key4': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key5': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
        }

    class Media:
        js = (
            # From root static directory
            "js/util.js",
            # From images static directory
            "js/ImageSourceFormHelper.js",
        )

    #error_css_class = ...
    #required_css_class = ...

    def clean(self):
        """
        1. Strip spaces from character fields.
        2. Location key processing: keep key n only if 1 through n-1
        are also specified.
        3. Call the parent's clean() to finish up with the default behavior.
        """

        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        if data['key1'] == u'':
            data['key2'] = u''
        if data['key2'] == u'':
            data['key3'] = u''
        if data['key3'] == u'':
            data['key4'] = u''
        if data['key4'] == u'':
            data['key5'] = u''

        self.cleaned_data = data

        return super(ImageSourceForm, self).clean()
