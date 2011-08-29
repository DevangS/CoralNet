from django.forms import Form, ModelForm, TextInput, FileInput, CharField
from django.forms.fields import ChoiceField, BooleanField, ImageField, FileField
from images.models import Source, Image, Metadata, Value1, Value2, Value3, Value4, Value5
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


class ImageUploadFormBasic(Form):
    files = ImageField(
        label='Image files',
        widget=FileInput(attrs={'multiple': 'multiple'}))


class ImageUploadForm(ImageUploadFormBasic):
    has_data_from_filenames = BooleanField(
        label='Collect metadata from filenames',
        required=False)

    def __init__(self, *args, **kwargs):
        """
        Dynamically generate help text for has_data_from_filenames.
        """
        source = kwargs.pop('source')
        super(ImageUploadForm, self).__init__(*args, **kwargs)

        sourceKeys = []
        sourceKeyExamples = []
        for key, exampleSuffix in [
                (source.key1, 'A'),
                (source.key2, ' 7'),
                (source.key3, ' 2-2'),
                (source.key4, 'C'),
                (source.key5, '1') ]:
            if key:
                sourceKeys.append(key)
                sourceKeyExamples.append(key + exampleSuffix)
        locKeysFormat = '_'.join(sourceKeys) + '_'
        locKeysExample = '_'.join(sourceKeyExamples) + '_'

        self.fields['has_data_from_filenames'].help_text = \
            "Required format: %sYYYY-MM-DD " % locKeysFormat + \
            "(Example: %s2010-08-23)" % locKeysExample


class ImageDetailForm(ModelForm):
    class Meta:
        model = Metadata
        fields = ('name', 'photo_date', 'value1', 'value2', 'value3',
                  'value4', 'value5', 'pixel_cm_ratio',
                  'camera', 'strobes', 'water_quality',
                  'photographer', 'description')

    def __init__(self, *args, **kwargs):
        """
        Dynamically generate the labels for the location value
        fields (the labels should be the Source's location keys),
        and delete unused value fields.
        """
        source = kwargs.pop('source')
        super(ImageDetailForm, self).__init__(*args, **kwargs)

        for key, valueField, valueClass in [
                (source.key1, 'value1', Value1),
                (source.key2, 'value2', Value2),
                (source.key3, 'value3', Value3),
                (source.key4, 'value4', Value4),
                (source.key5, 'value5', Value5)
                ]:
            if key:
                # Create a choices iterable of all of this Source's values as
                # well as an 'Other' value
                
                # Not sure why I need to specify the '' choice here;
                # I thought required=False for the ChoiceField would automatically create this... -Stephen
                choices = [('', '---------')]
                valueObjs = valueClass.objects.filter(source=source).order_by('name')
                for valueObj in valueObjs:
                    choices.append((valueObj.id, valueObj.name))
                choices.append(('OtherId', 'Other'))

                self.fields[valueField] = ChoiceField(choices, label=key, required=False)

                # Add a text input field for specifying the Other choice
                pos = self.fields.keyOrder.index(valueField)

                self.fields.insert(pos+1, valueField + '_other',
                                   CharField(label='Other',
                                             max_length=valueClass._meta.get_field('name').max_length,
                                             required=False,
                                             #TODO: Make the Other textbox actually float to the right of the dropdown list
                                             widget=TextInput(attrs={'style': 'float:right'})
                                   )
                )
            else:
                del self.fields[valueField]

    def clean(self):
        """
        1. Strip spaces from character fields.
        2. Handle the location values.
        3. Call the parent's clean() to finish up with the default behavior.
        """
        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        image = Image.objects.get(metadata=self.instance)
        source = image.source

        # Right now, the valueN field's value is the integer id
        # of a ValueN object. We want the ValueN object.
        for key, valueField, valueClass in [
            (source.key1, 'value1', Value1),
            (source.key2, 'value2', Value2),
            (source.key3, 'value3', Value3),
            (source.key4, 'value4', Value4),
            (source.key5, 'value5', Value5) ]:

            # Make sure the form actually has this valueN.
            if data.has_key(valueField):

                # This field's value is blank, so set object to None.
                if not data[valueField]:
                    data[valueField] = None

                # "Other" was chosen.
                elif data[valueField] == 'OtherId':
                    otherValue = data[valueField + '_other']
                    if not otherValue:
                        # Error
                        msg = u"If you select Other, you must specify the %s below." % key
                        self._errors[valueField + '_other'] = self.error_class([msg])
                        data[valueField] = None
                    else:
                        # Add new value to database, or get it if it already exists
                        # (the latter case would be the user not noticing it was already in the choices).
                        # **NOTE: Make sure the view function using this form rolls back
                        # any object creation if the form has errors.
                        newValueObj, created = valueClass.objects.get_or_create(name=otherValue, source=source)
                        data[valueField] = newValueObj

                # Set to ValueN object of the given id.
                else:
                    data[valueField] = valueClass.objects.get(pk=data[valueField])

            
        self.cleaned_data = data
        return super(ImageDetailForm, self).clean()


class AnnotationImportForm(Form):
    annotations_file = FileField(
        label='Annotation file (.txt)',
    )
