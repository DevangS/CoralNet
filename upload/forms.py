from django import forms
from django.core.exceptions import ValidationError
from django.forms import FileInput, ImageField, Form, ChoiceField, FileField, CharField, BooleanField, TextInput, DateField, HiddenInput
from django.utils.translation import ugettext_lazy as _
from lib.forms import clean_comma_separated_image_ids_field
from upload.utils import metadata_to_filename
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Image
from datetime import date

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

        general_content_type = anno_file.content_type.split('/')[0]
        if general_content_type != 'text':
            raise ValidationError("This file is not a text file.")

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
    This form is used to edit the metadata of images within this source. This is commonly used within
    a form set whenever it is used.
    """
    date = DateField(required=False, widget= TextInput(attrs={'size': 8,}))
    height = CharField(widget= TextInput(attrs={'size': 10,}))
    latitude = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    longitude = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    depth = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    camera = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    photographer = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    waterQuality = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    strobes = CharField(required=False, widget= TextInput(attrs={'size': 10,}))
    framingGear = CharField(required=False, widget= TextInput(attrs={'size': 16,}))
    whiteBalance = CharField(required=False, widget= TextInput(attrs={'size': 16,}))

    def __init__(self, *args, **kwargs):
        self.source_id = kwargs.pop('source_id')
        super(MetadataForm,self).__init__(*args, **kwargs)
        self.source = Source.objects.get(pk=self.source_id)

        # Need to create fields for keys based on the number of keys in this source.
        #
        # Using insert so that the fields appear in the right order on the
        # page. This field order should match the order of the table headers
        # in the page template.
        for key_num in range(1, self.source.num_of_keys()+1):
            self.fields.insert(
                key_num,
                'key%s' % key_num,
                CharField(required=False, widget=TextInput(attrs={'size': 10,}))
            )

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

    def clean_annotations_file(self):
        csv_file = self.cleaned_data['csv_file']

        general_content_type = csv_file.content_type.split('/')[0]
        if general_content_type != 'csv':
            raise ValidationError("This file is not a csv file.")

        return self.cleaned_data['csv_file']


#class ProceedToManageMetadataForm(Form):
#    """
#    This form is shown after an upload completes. When the form is
#    submitted, the user proceeds to the metadata-edit page, where
#    the grid is populated with the images that were just uploaded.
#
#    To do this, this form has a hidden field that contains the ids
#    of all the images that were just uploaded. The metadata grid view
#    then uses this field to determine which images to show.
#    """
#
#    # The ids of the images in this upload, as a
#    # comma-separated string.
#    uploaded_image_ids = CharField(widget=HiddenInput())
#
#    def __init__(self, *args, **kwargs):
#        self.source = kwargs.pop('source')
#        super(ProceedToManageMetadataForm,self).__init__(*args, **kwargs)
#
#    def clean_uploaded_image_ids(self):
#        self.cleaned_data['uploaded_image_ids'] = \
#            clean_comma_separated_image_ids_field(
#                self.cleaned_data['uploaded_image_ids'],
#                self.source,
#            )
#        return self.cleaned_data['uploaded_image_ids']
