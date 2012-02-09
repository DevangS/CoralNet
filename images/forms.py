from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm, TextInput, FileInput, CharField
from django.forms.fields import ChoiceField, BooleanField, ImageField, FileField, IntegerField
from django.forms.widgets import Select
from images.models import Source, Image, Metadata, Value1, Value2, Value3, Value4, Value5, SourceInvite
from CoralNet.forms import FormHelper
from images.utils import PointGen, metadata_to_filename

class ImageSourceForm(ModelForm):

    class Meta:
        model = Source
        exclude = ('default_point_generation_method', 'labelset')
        widgets = {
            'key1': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key2': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key3': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key4': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'key5': TextInput(attrs={'onkeyup': 'ImageSourceFormHelper.changeKeyFields()'}),
            'image_height_in_cm': TextInput(attrs={'size': 3}),
            'longitude': TextInput(attrs={'size': 10}),
            'latitude': TextInput(attrs={'size': 10}),
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

    def __init__(self, *args, **kwargs):

        super(ImageSourceForm, self).__init__(*args, **kwargs)

        # For use in templates.  Can iterate over fieldsets instead of the entire form.
        self.fieldsets = {'general_info': [self[name] for name in ['name', 'visibility', 'description']],
                          'keys': [self[name] for name in ['key1', 'key2', 'key3', 'key4', 'key5']],
                          'image_annotation': [self[name] for name in ['image_height_in_cm']],
                          'world_location': [self[name] for name in ['latitude', 'longitude']]}


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


class SourceInviteForm(Form):
    # This is not a ModelForm, because a ModelForm would by default
    # make us use a dropdown/radiobutton for the recipient field,
    # and it would validate that the recipient field's value is a
    # foreign key id.  This is a slight pain to work around if we
    # want a text box for the recipient field, so it's easier
    # to just use a Form.

    recipient = CharField(max_length=User._meta.get_field('username').max_length,
                          help_text="The recipient's username.")
    source_perm = ChoiceField(label='Permission level',
                              choices=SourceInvite._meta.get_field('source_perm').choices)

    def __init__(self, *args, **kwargs):
        self.source_id = kwargs.pop('source_id')
        super(SourceInviteForm, self).__init__(*args, **kwargs)

    def clean_recipient(self):
        """
        This method cleans the recipient field of a submitted form.
        It is automatically called during form validation.

        1. Strip spaces.
        2. Check that we have a valid recipient username.
        If so, replace the username with the recipient user's id.
        If not, throw an error.
        """

        recipientUsername = self.cleaned_data['recipient']
        recipientUsername = recipientUsername.strip()

        try:
            User.objects.get(username=recipientUsername)
        except User.DoesNotExist:
            raise ValidationError("There is no user with this username.")

        return recipientUsername

    def clean(self):
        """
        Looking at both the recipient and the source, see if we have an
        error case:
        (1) The recipient is already a member of the source.
        (2) The recipient has already been invited to the source.
        """

        if not self.cleaned_data.has_key('recipient'):
            return super(SourceInviteForm, self).clean()

        recipientUser = User.objects.get(username=self.cleaned_data['recipient'])
        source = Source.objects.get(pk=self.source_id)

        if source.has_member(recipientUser):
            msg = u"%s is already in this Source." % recipientUser.username
            self._errors['recipient'] = self.error_class([msg])
            return super(SourceInviteForm, self).clean()

        try:
            SourceInvite.objects.get(recipient=recipientUser, source=source)
        except SourceInvite.DoesNotExist:
            pass
        else:
            msg = u"%s has already been invited to this Source." % recipientUser.username
            self._errors['recipient'] = self.error_class([msg])

        return super(SourceInviteForm, self).clean()


class ImageUploadForm(Form):
    files = ImageField(
        label='Image files',
        widget=FileInput(attrs={'multiple': 'multiple'}))
    #TODO: Add helptext saying which file formats are acceptable.


class ImageUploadOptionsForm(Form):
    """
    Helper form for the ImageUploadForm.
    Has options such as choosing to skip or replace duplicate images.
    """
    class Media:
        css = {
            'all': ("css/uploadForm.css",)
        }
        js = (
            # From root static directory
            "js/util.js",
            # From annotations static directory
            "js/ImageUploadFormHelper.js",
        )

    specify_metadata = ChoiceField(
        label='How to specify metadata',
        help_text='',  # To be filled in by the form constructor
        choices=(('filenames', 'From filenames'),),
        initial='filenames',
        required=True)

    skip_or_replace_duplicates = ChoiceField(
        label='Skip or replace duplicate images',
        help_text="Skip (don't upload) or replace (re-upload) images that have duplicates in your Source.\n"
                  "Duplicates are defined as images with the same location keys and year.",
        choices=(('skip', 'Skip'), ('replace', 'Replace')),
        required=True)

    def __init__(self, *args, **kwargs):
        """
        (1) Dynamically generate help text.
        (2) If the source doesn't have a point generation method specified, then remove the
        "will_generate_points" checkbox from the form.
        """
        source = kwargs.pop('source')
        super(ImageUploadOptionsForm, self).__init__(*args, **kwargs)

        # Dynamically generate help text.
        # Show the filename format that should be used,
        # and an example of a filename adhering to that format.
        filenameFormatArgs = dict(year='YYYY', month='MM', day='DD')
        filenameExampleArgs = dict(year='2010', month='08', day='23')

        sourceKeys = source.get_key_list()
        exampleSuffixes = ['A', ' 7', ' 2-2', 'C', '1'][0 : len(sourceKeys)]

        filenameFormatArgs['values'] = sourceKeys
        filenameExampleArgs['values'] = [a+b for a,b in zip(sourceKeys, exampleSuffixes)]

        filenameFormatStr = metadata_to_filename(**filenameFormatArgs)
        filenameExampleStr = metadata_to_filename(**filenameExampleArgs) + ".jpg"

        self.fields['specify_metadata'].help_text = \
            "Required filename format: %s" % filenameFormatStr

        # Use JavaScript to show/hide this additional help text
        self.metadata_extra_help_text = (
            "\n"
            "For example, let's say your source has the following location keys: "
            "Site, Depth, Transect Line and Quadrant. "
            "If you want to upload a .jpg image that was taken at "
            "Site: sharkPoint, Depth: 10m, Transect Line: 3, and Quadrant: qu4, "
            "on 14 January 2010, the filename for upload should be:\n\n"

            "sharkPoint_10m_3_qu4_2010-01-14.jpg\n\n"

            "Alternatively, if you also want to store the original filename - say it's "
            "IMG_0032.jpg - you can use:\n\n"

            "sharkPoint_10m_3_qu4_2010-01-14_IMG_0032.jpg\n\n"

            "The original file name is not used by CoralNet, but could be "
            "useful for your own reference."
        )


        # TODO: For correctness, make sure this only applies to the
        # regular image upload form, not the image+annotation import form.
        self.additional_details = [
            """Annotation points will be automatically generated for your images.
            Your Source's point generation settings: %s""" % PointGen.db_to_readable_format(source.default_point_generation_method)
        ]


class ImageDetailForm(ModelForm):
    class Meta:
        model = Metadata
        exclude = ('group1_percent', 'group2_percent', 'group3_percent',
                   'group4_percent', 'group5_percent', 'group6_percent', 'group7_percent')

    class Media:
        js = (
            # Collected from root static directory
            "js/util.js",
            # Collected from app-specific static directory
            "js/ImageDetailFormHelper.js",
        )

    def __init__(self, *args, **kwargs):
        """
        Dynamically generate the labels for the location value
        fields (the labels should be the Source's location keys),
        and delete unused value fields.
        """
        source = kwargs.pop('source')
        super(ImageDetailForm, self).__init__(*args, **kwargs)

        valueFields = []

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
                choices.append(('Other', 'Other (Specify)'))

                self.fields[valueField] = ChoiceField(choices, label=key, required=True)

                # Add a text input field for specifying the Other choice
                self.fields[valueField + '_other'] = CharField(
                    label='Other',
                    max_length=valueClass._meta.get_field('name').max_length,
                    required=False
                )

                valueFields += [valueField, valueField + '_other']

            else:
                # If the key isn't in the source, just remove the
                # corresponding value field from the form
                del self.fields[valueField]

        # For use in templates.  Can iterate over fieldsets instead of the entire form.
        self.fieldsets = {'keys': [self[name] for name in (['photo_date'] + valueFields)],
                          'annotation_related': [self[name] for name in ['height_in_cm']],
                          'other_info': [self[name] for name in ['name', 'latitude', 'longitude', 'depth',
                                                                 'camera', 'photographer',
                                                                 'water_quality', 'strobes', 'framing',
                                                                 'balance', 'comments']] }

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

                # "Other" was chosen.
                if data[valueField] == 'Other':
                    otherValue = data[valueField + '_other']
                    if not otherValue:
                        # Error
                        msg = u"Since you selected Other, you must use this text box to specify the %s." % key
                        self._errors[valueField + '_other'] = self.error_class([msg])

                        # TODO: Make this not a hack.  This sets the valueField to be some arbitrary non-blank
                        # valueN object, so (1) we won't get an error on clean() about 'Other'
                        # not being a valueClass object, and (2) we won't get a
                        # "field cannot be blank" error on the dropdown.
                        # One possible consequence of this hack is that it'll crash if there are no valueClass objects of that value number on the site yet. (e.g. no value5s)
                        data[valueField] = valueClass.objects.all()[0]
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


class PointGenForm(Form):

    class Media:
        js = (
            # From root static directory
            "js/util.js",
            # From annotations static directory
            "js/PointGenFormHelper.js",
        )

    MAX_NUM_POINTS = 1000

    point_generation_type = ChoiceField(
        label='Point generation type',
        choices=Source.POINT_GENERATION_CHOICES,
        widget=Select(attrs={'onchange': 'PointGenFormHelper.showOnlyRelevantFields()'}),
    )

    # The following fields may or may not be required depending on the
    # point_generation_type. We'll make all of them required by default,
    # then in clean(), we'll ignore the errors for fields that
    # we decide are not required.

    # For simple random
    simple_number_of_points = IntegerField(
        label='Number of annotation points', required=True,
        min_value=1, max_value=MAX_NUM_POINTS,
        widget=TextInput(attrs={'size': 3}),
    )

    # For stratified random and uniform grid
    number_of_cell_rows = IntegerField(
        label='Number of cell rows', required=True,
        min_value=1, max_value=MAX_NUM_POINTS,
        widget=TextInput(attrs={'size': 3}),
    )
    number_of_cell_columns = IntegerField(
        label='Number of cell columns', required=True,
        min_value=1, max_value=MAX_NUM_POINTS,
        widget=TextInput(attrs={'size': 3}),
    )

    # For stratified random
    stratified_points_per_cell = IntegerField(
        label='Points per cell', required=True,
        min_value=1, max_value=MAX_NUM_POINTS,
        widget=TextInput(attrs={'size': 3}),
    )

    def __init__(self, *args, **kwargs):
        """
        If a Source is passed in as an argument, then get
        the point generation method of that Source,
        and use that to fill the form fields' initial values.
        """
        if kwargs.has_key('source'):
            source = kwargs.pop('source')
            kwargs['initial'] = PointGen.db_to_args_format(source.default_point_generation_method)

        super(PointGenForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = self.cleaned_data
        type = data['point_generation_type']

        # Depending on the point generation type that was picked, different
        # fields are going to be required or not. Identify the required fields
        # (other than the point-gen type).
        additional_required_fields = []
        if type == PointGen.Types.SIMPLE:
            additional_required_fields = ['simple_number_of_points']
        elif type == PointGen.Types.STRATIFIED:
            additional_required_fields = ['number_of_cell_rows', 'number_of_cell_columns', 'stratified_points_per_cell']
        elif type == PointGen.Types.UNIFORM:
            additional_required_fields = ['number_of_cell_rows', 'number_of_cell_columns']

        # Get rid of errors for the fields we don't care about.
        required_fields = ['point_generation_type'] + additional_required_fields
        for key in self._errors.keys():
            if key not in required_fields:
                del self._errors[key]

        # If there are no errors so far, do a final check of
        # the total number of points specified.
        # It should be between 1 and MAX_NUM_POINTS.
        if len(self._errors) == 0:

            num_points = 0
            if type == PointGen.Types.SIMPLE:
                num_points = data['simple_number_of_points']
            elif type == PointGen.Types.STRATIFIED:
                num_points = data['number_of_cell_rows'] * data['number_of_cell_columns'] * data['stratified_points_per_cell']
            elif type == PointGen.Types.UNIFORM:
                num_points = data['number_of_cell_rows'] * data['number_of_cell_columns']

            if num_points > PointGenForm.MAX_NUM_POINTS:
                raise ValidationError("You specified %s points total. Please make it no more than %s." % (num_points, PointGenForm.MAX_NUM_POINTS))

        self.cleaned_data = data
        return super(PointGenForm, self).clean()


class AnnotationImportForm(Form):
    annotations_file = FileField(
        label='Annotation file (.txt)',
    )

class LabelImportForm(Form):
    labelset_description = CharField(
        label='Labelset description',
    )

    labels_file = FileField(
        label='Labels file (.txt)',
    )
