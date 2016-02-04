from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms import FileInput, ImageField, Form, ChoiceField, FileField, CharField, BooleanField, TextInput, DateField, HiddenInput
from django.utils.translation import ugettext_lazy as _
from upload.utils import metadata_to_filename
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata, ImageModelConstants, LocationValue

class MultipleFileInput(FileInput):
    """
    Modifies the built-in FileInput widget by allowing validation of multi-file input.
    (When FileInput takes multiple files, it only validates the last one.)
    """
    def __init__(self, attrs=None):
        # Include the attr multiple = 'multiple' by default.
        # (For reference, TextArea.__init__ adds default attrs in the same way.)
        default_attrs = {'multiple': 'multiple'}
        if attrs is not None:
            default_attrs.update(attrs)
        super(MultipleFileInput, self).__init__(attrs=default_attrs)

    def value_from_datadict(self, data, files, name):
        """
        FileInput's method only uses get() here, which means only 1 file is gotten.
        We need getlist to get all the files.
        """
        if not files:
            # files is the empty dict {} instead of a MultiValueDict.
            # That will happen if the files parameter passed into the
            # form is an empty MultiValueDict, because Field.__init__()
            # has the code 'self.files = files or {}'.
            return []
        else:
            # In any other case, we'll have a MultiValueDict, which has
            # the method getlist() to get the values as a list.
            return files.getlist(name)


class MultipleImageField(ImageField):
    """
    Modifies the built-in ImageField by allowing validation of multi-file input.
    (When ImageField takes multiple files, it only validates the last one.)

    Must be used with the MultipleFileInput widget.
    """

    def to_python(self, data):
        """
        Checks that each file of the file-upload field data contains a valid
        image (GIF, JPG, PNG, possibly others -- whatever the Python Imaging
        Library supports).
        """
        data_out = []

        for list_item in data:
            try:
                f = super(MultipleImageField, self).to_python(list_item)
            except ValidationError, err:
                raise ValidationError(err.messages[0])
            data_out.append(f)

        return data_out


class MultiImageUploadForm(Form):
    """
    Takes multiple image files.

    This is used only for the frontend of the image upload form.
    """
    files = MultipleImageField(
        label='Image files',
        widget=MultipleFileInput(),
    )

    def __init__(self, *args, **kwargs):
        """
        - Add extra_help_text to the file field.
        """
        super(MultiImageUploadForm, self).__init__(*args, **kwargs)

        # This field's help text will go in a separate template, which
        # can be displayed in a modal dialog.
        self.fields['files'].dialog_help_text_template = \
            'upload/help_image_files.html'


class ImageUploadForm(Form):
    """
    Takes a single image file.

    This is used only for the backend of the image upload form.
    """
    file = ImageField(
        label='Image file',
        widget=FileInput(),
        error_messages={
            'invalid_image': _(u"The file is either a corrupt image, or in a file format that we don't support."),
        },
    )

# Remnants of an attempt at a progress bar...

# Upload id field for tracking the upload progress.
#
# Might need to ensure the input element's name is X-Progress-ID in
# order to get this working with UploadProgressCacheHandler, which
# demands that exact name.  Not sure where UPCH got that name came
# from, but it might have something to do with nginx.
#
# Is it even necessary to have this upload id in the form class?
# It seems that UploadProgressCachedHandler.handle_raw_input() looks
# for the upload id as a GET parameter only (and Django fields are only
# needed for POST parameters).
# http://www.laurentluce.com/posts/upload-to-django-with-progress-bar-using-ajax-and-jquery/#comment-1192

#    ajax_upload_id = CharField(
#        label='',
#        widget=HiddenInput(),
#    )


class ImageUploadOptionsForm(Form):
    """
    Helper form for the ImageUploadForm.
    """

    specify_metadata = ChoiceField(
        label='Specify image metadata',
        help_text='',  # To be filled in by the form's __init__()
        choices=(
            ('after', 'Later (after upload)'),
            ('filenames', 'In the image filenames'),
            ('csv', 'From a CSV file')
        ),
        initial='after',
        required=True
    )

    def __init__(self, *args, **kwargs):

        source = kwargs.pop('source')
        super(ImageUploadOptionsForm, self).__init__(*args, **kwargs)

        # Dynamically generate a source-specific string for the metadata
        # field's help text.
        filename_format_args = dict(year='YYYY', month='MM', day='DD')
        source_keys = source.get_key_list()
        filename_format_args['values'] = source_keys

        self.fields['specify_metadata'].source_specific_filename_format =\
        metadata_to_filename(**filename_format_args)

        # This field's help text will go in a separate template, which
        # can be displayed in a modal dialog.
        self.fields['specify_metadata'].dialog_help_text_template = \
            'upload/help_specify_metadata.html'


class AnnotationImportForm(Form):
    annotations_file = FileField(
        label='Points/Annotations file (.txt)',
    )

    def __init__(self, *args, **kwargs):
        """
        Add extra_help_text to the file field.
        """
        super(AnnotationImportForm, self).__init__(*args, **kwargs)

        # This field's help text will go in a separate template, which
        # can be displayed in a modal dialog.
        self.fields['annotations_file'].dialog_help_text_template = \
            'upload/help_annotations_file.html'

    def clean_annotations_file(self):
        anno_file = self.cleaned_data['annotations_file']

        # Naively validate that the file is a text file through
        # (1) given MIME type, or (2) file extension.  Either of them
        # can be faked though.
        #
        # For the file extension check, would be more "correct" to use:
        # mimetypes.guess_type(csv_file.name).startswith('text/')
        # but the mimetypes module doesn't recognize csv for
        # some reason.
        if anno_file.content_type.startswith('text/'):
            pass
        elif anno_file.name.endswith('.txt'):
            pass
        else:
            raise ValidationError("This file is not a plain text file.")

        return self.cleaned_data['annotations_file']


class AnnotationImportOptionsForm(Form):
    """
    Helper form for the AnnotationImportForm, containing import options.
    """
    is_uploading_points_or_annotations = forms.fields.BooleanField(
        required=False,
    )

    is_uploading_annotations_not_just_points = ChoiceField(
        label='Data',
        choices=(
            ('yes', "Points and annotations"),
            ('no', "Points only"),
        ),
        initial='yes',
    )

    def __init__(self, *args, **kwargs):
        """
        Add extra_help_text to the file field.
        """
        source = kwargs.pop('source')
        super(AnnotationImportOptionsForm, self).__init__(*args, **kwargs)

        if source.labelset.isEmptyLabelset():
            self.fields['is_uploading_annotations_not_just_points'].choices = (
                ('no', "Points only"),
            )
            self.fields['is_uploading_annotations_not_just_points'].initial = 'no'
            self.fields['is_uploading_annotations_not_just_points'].help_text = (
                "This source doesn't have a labelset yet, so you can't upload annotations."
            )

    def clean_is_uploading_annotations_not_just_points(self):
        field_name = 'is_uploading_annotations_not_just_points'
        option = self.cleaned_data[field_name]

        if option == 'yes':
            self.cleaned_data[field_name] = True
        elif option == 'no':
            self.cleaned_data[field_name] = False
        else:
            raise ValidationError("Unknown value for {field_name}".format(field_name=field_name))

        return self.cleaned_data[field_name]

class CheckboxForm(Form):
    """
    This is used in conjunction with the metadataForm; but since the metadata form is rendered as
    a form set, and I only want one select all checkbox, this form exists.
    """
    selected = BooleanField(required=False)

class MetadataForm(Form):
    """
    This form is used to edit the metadata of an image within a source.

    This is commonly used within a form set, so that multiple images can
    be edited at once.
    """
    image_id = forms.IntegerField(widget=forms.HiddenInput())
    photo_date = DateField(required=False, widget= TextInput(attrs={'size': 8,}))
    height_in_cm = forms.IntegerField(
        min_value=ImageModelConstants.MIN_IMAGE_CM_HEIGHT,
        max_value=ImageModelConstants.MAX_IMAGE_CM_HEIGHT,
        widget=TextInput(attrs={'size': 10,}),
    )
    latitude = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    longitude = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    depth = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    camera = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    photographer = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    water_quality = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    strobes = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    framing = CharField(required=False, widget= TextInput(attrs={'size': 16,}))
    balance = CharField(required=False, widget= TextInput(attrs={'size': 16,}))

    def __init__(self, *args, **kwargs):
        self.source_id = kwargs.pop('source_id')
        super(MetadataForm,self).__init__(*args, **kwargs)
        self.source = Source.objects.get(pk=self.source_id)

        # Need to create fields for keys based on the number of keys in this source.
        #
        # Using insert so that the fields appear in the right order on the
        # page. This field order should match the order of the table headers
        # in the page template.
        key_list = self.source.get_key_list()
        location_value_max_length = LocationValue._meta.get_field('name').max_length
        date_field_index = 1
        for key_num in range(1, len(key_list)+1):
            self.fields.insert(
                date_field_index + key_num,
                'key%s' % key_num,
                CharField(
                    required=False,
                    widget=TextInput(attrs={'size': 10, 'maxlength': location_value_max_length}),
                    label=key_list[key_num-1],
                    max_length=location_value_max_length,
                )
            )

        # Apply labels and max-length attributes from the Metadata model to the
        # form fields (besides the key fields, which we already did).
        #
        # This could be done automatically if this were a ModelForm instead of a
        # regular Form. Whether a ModelForm makes things cleaner overall remains
        # to be seen.
        char_fields = ['latitude', 'longitude', 'depth', 'camera',
                       'photographer', 'water_quality', 'strobes',
                       'framing', 'balance']
        editable_fields = ['photo_date', 'height_in_cm'] + char_fields

        for field_name in editable_fields:
            form_field = self.fields[field_name]
            form_field.label = Metadata._meta.get_field(field_name).verbose_name

        for field_name in char_fields:

            form_field = self.fields[field_name]
            max_length = Metadata._meta.get_field(field_name).max_length

            # If we were setting the max length through the CharField's
            # __init__(), we could probably just set field.max_length and be
            # done.  But since we're past __init__(), we have to do a bit more
            # manual work.

            # Set a max-length validator.
            #
            # It seems that validators are shared among all instances of a
            # form class, even if the validators are added dynamically. So to
            # avoid adding duplicates of the same MaxLengthValidator, we'll
            # first check if the field already has such a validator. If it
            # does, we do nothing. If it doesn't, we add a MaxLengthValidator.
            if not any([isinstance(v, validators.MaxLengthValidator)
                        for v in form_field.validators]):
                form_field.validators.append(
                    validators.MaxLengthValidator(max_length)
                )

            # Make it impossible to type more than max_length characters in
            # the HTML input element. (Impossible without something like
            # Inspect Element HTML editing, that is)
            form_field.widget.attrs.update({'maxlength': max_length})


    def clean(self):
        data = self.cleaned_data

        # Parse key entries as Value objects.
        key_fields = ['key1', 'key2', 'key3', 'key4', 'key5']
        value_models = [Value1, Value2, Value3, Value4, Value5]
        for key_field, value_model in zip(key_fields, value_models):
            if key_field in data:
                # This key field is in the form. (key5 won't be there
                # if the source has only 4 keys)
                if data[key_field] == '':
                    # If the field value is empty, don't try to make an
                    # empty-string Value object. Set it to None instead.
                    data[key_field] = None
                else:
                    newValueObj, created = value_model.objects.get_or_create(
                        name=data[key_field],
                        source=self.source
                    )
                    data[key_field] = newValueObj

        return super(MetadataForm, self).clean()


class MetadataImportForm(forms.ModelForm):
    """
    Form used to import metadata from CSV.

    This need not be completely different from MetadataForm, which is used
    to edit metadata in a formset. Perhaps there is enough overlap in these
    forms' functionality that they can share fields/attributes in a
    superclass.
    """
    class Meta:
        model = Metadata
        fields = ['photo_date', 'value1', 'value2', 'value3', 'value4',
                  'value5', 'height_in_cm', 'latitude', 'longitude',
                  'depth', 'camera', 'photographer', 'water_quality',
                  'strobes', 'framing', 'balance']

    def __init__(self, source_id, save_new_values, *args, **kwargs):

        super(MetadataImportForm, self).__init__(*args, **kwargs)
        self.source = Source.objects.get(pk=source_id)
        self.save_new_values = save_new_values

        # Replace location value fields to make them CharFields instead of
        # ModelChoiceFields. Also, remove location value fields that
        # the source doesn't need.
        #
        # The main reason we still specify the value fields in Meta.fields is
        # to make it easy to specify the fields' ordering.
        key_list = self.source.get_key_list()
        location_value_max_length = LocationValue._meta.get_field('name').max_length

        for value_num in [1,2,3,4,5]:

            value_field = 'value'+str(value_num)

            if len(key_list) >= value_num:
                self.fields[value_field] = CharField(
                    required=False,
                    label=key_list[value_num-1],
                    max_length=location_value_max_length,
                )
            else:
                del self.fields[value_field]

    def clean(self):
        data = self.cleaned_data

        # Parse key entries as Value objects.
        value_fields = ['value1', 'value2', 'value3', 'value4', 'value5']
        value_models = [Value1, Value2, Value3, Value4, Value5]
        for value_field, value_model in zip(value_fields, value_models):
            if value_field in data:
                # This value field is in the form. (value5 won't be there
                # if the source has only 4 keys)
                if data[value_field] == '':
                    # If the field value is empty, don't try to make an
                    # empty-string Value object. Set it to None instead.
                    data[value_field] = None
                else:
                    try:
                        value_obj = value_model.objects.get(
                            name=data[value_field],
                            source=self.source
                        )
                    except value_model.DoesNotExist:
                        # If the desired location value doesn't exist, then
                        # make our own Value object.
                        value_obj = value_model(name=data[value_field], source=self.source)
                        if self.save_new_values:
                            value_obj.save()
                    data[value_field] = value_obj

        return super(MetadataImportForm, self).clean()


class CSVImportForm(Form):
    csv_file = FileField(
        label='CSV file',
    )

    def __init__(self, *args, **kwargs):
        """
        Add extra_help_text to the file field.
        """
        super(CSVImportForm, self).__init__(*args, **kwargs)

        self.fields['csv_file'].dialog_help_text_template =\
            'upload/help_csv_file.html'

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']

        # Naively validate that the file is a CSV file through
        # (1) given MIME type, or (2) file extension.  Either of them
        # can be faked though.
        #
        # For the file extension check, would be more "correct" to use:
        # mimetypes.guess_type(csv_file.name) == 'text/csv'
        # but the mimetypes module doesn't recognize csv for
        # some reason.
        if csv_file.content_type == 'text/csv':
            pass
        elif csv_file.name.endswith('.csv'):
            pass
        else:
            raise ValidationError("This file is not a CSV file.")

        return self.cleaned_data['csv_file']




class ImportArchivedAnnotationsForm(Form):
    csv_file = FileField(
        label='CSV file TEST',
    )
    is_uploading_annotations_not_just_points = ChoiceField(
        label='Data',
        choices=(
            (True, "Points and annotations"),
            (False, "Points only"),
        ),
        initial=True,
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']

        # Naively validate that the file is a CSV file through
        # (1) given MIME type, or (2) file extension.  Either of them
        # can be faked though.
        #
        # For the file extension check, would be more "correct" to use:
        # mimetypes.guess_type(csv_file.name) == 'text/csv'
        # but the mimetypes module doesn't recognize csv for
        # some reason.
        if csv_file.content_type == 'text/csv':
            pass
        elif csv_file.name.endswith('.csv'):
            pass
        else:
            raise ValidationError("This file is not a CSV file.")

        return self.cleaned_data['csv_file']
