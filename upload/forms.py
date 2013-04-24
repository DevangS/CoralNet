from django import forms
from django.core.exceptions import ValidationError
from django.forms import FileInput, ImageField, Form, ChoiceField, FileField, CharField, BooleanField, TextInput, DateField
from django.utils.translation import ugettext_lazy as _
from upload.utils import metadata_to_filename
from images.models import Source, Value1, Value2, Value3, Value4, Value5
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

        self.fields['files'].extra_help_text = (
            "Accepted file formats: JPG, PNG, GIF, and possibly others.\n"
            "You can select multiple files, but you can only select files within a single folder.\n"
            "Tip: When selecting files, click inside the folder area and then hit Ctrl+A (or Cmd+A for Mac) to select all files in that folder."
        )


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
            ('after', 'After upload'),
            ('filenames', 'In the image filenames'),
            ('csv', 'From CSV file')
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

        self.fields['annotations_file'].extra_help_text = (
            "The points/annotations file is a text file. Each line of text "
            "should correspond to one point/annotation. Here is the format "
            "for each line:\n"
            "\n"
            "location value 1; value 2; ... ; value n; year; row; column[; label code]\n"
            "\n"
            "An example:\n"
            "- Your source has the following location keys: Site, Depth, "
            "Transect Line and Quadrant.\n"
            "- You are uploading an image that was taken at Site: sharkPoint, "
            "Depth: 10m, Transect Line: 3, and Quadrant: qu4, on 14 January "
            "2010.\n"
            "- You want to specify a point for this image that is on the "
            "100th row and 150th column of the image (with rows and columns "
            "measured in pixels).\n"
            "- That point should be annotated with a label whose short code "
            "is Porit.\n"
            "\n"
            "Then you will have the following line of text:\n"
            "\n"
            "sharkPoint; 10m; 3; qu4; 2010; 100; 150; Porit\n"
            "\n"
            "If you are uploading points only and not annotations, then your "
            "line of text may specify a label code anyway (which will be "
            "ignored), or you may omit the label code like so:\n"
            "\n"
            "sharkPoint; 10m; 3; qu4; 2010; 100; 150\n"
            "\n"
            "Notes:\n"
            "- When you choose a points/annotations file, it automatically "
            "gets processed. If the processing results are not what you "
            "expect, you can make corrections to the file and then click the "
            "\"Re-process file\" button to process the file again.\n"
            "If the file contains points/annotations for an image that is not "
            "selected for upload below, those particular points/annotations "
            "will simply be ignored at upload time.\n"
            "- If you're used to expressing point positions with x and y, "
            "note that x corresponds to columns, and y corresponds to rows.\n"
            "- If your image is 1000 pixels wide, then the possible column "
            "numbers are 1-1000, not 0-999. The same thing applies to row "
            "numbers.\n"
            "- Label codes in the points/annotations file must correspond to "
            "a label in your source's labelset.\n"
            "- Label codes are case-insensitive. If your labelset has a label "
            "code PORIT, and the points/annotations file has Porit, then "
            "these codes will match.\n"
        )

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
    selected = BooleanField(required=False)
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

        # Need to create fields for keys based on the number that exist in this source.
        # Using insert so that the fields appear in the right order.
        for j in range(self.source.num_of_keys()):
            self.fields.insert(j+2,'key%s' % (j+1), CharField(required=False, widget= TextInput(attrs={'size': 10,})));

    def clean(self):
        data = self.cleaned_data

        # Parse key entries as Value objects.
        if 'key1' in data:
            newValueObj, created = Value1.objects.get_or_create(name=data['key1'], source=self.source)
            data['key1'] = newValueObj
        if 'key2' in data:
            newValueObj, created = Value2.objects.get_or_create(name=data['key2'], source=self.source)
            data['key2'] = newValueObj
        if 'key3' in data:
            newValueObj, created = Value3.objects.get_or_create(name=data['key3'], source=self.source)
            data['key3'] = newValueObj
        if 'key4' in data:
            newValueObj, created = Value4.objects.get_or_create(name=data['key4'], source=self.source)
            data['key4'] = newValueObj
        if 'key5' in data:
            newValueObj, created = Value5.objects.get_or_create(name=data['key5'], source=self.source)
            data['key5'] = newValueObj

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

        self.fields['csv_file'].extra_help_text = (
            "This is placeholder help text!\n"
            )

    def clean_annotations_file(self):
        csv_file = self.cleaned_data['csv_file']

        general_content_type = csv_file.content_type.split('/')[0]
        if general_content_type != 'csv':
            raise ValidationError("This file is not a csv file.")

        return self.cleaned_data['csv_file']
