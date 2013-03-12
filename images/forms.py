from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm
from django.forms import fields
from django.forms.fields import CharField, ChoiceField, FileField, IntegerField
from django.forms.widgets import  Select, TextInput
from images.models import Source, Image, Metadata, Value1, Value2, Value3, Value4, Value5, SourceInvite
from CoralNet.forms import FormHelper
from images.model_utils import PointGen
from lib import str_consts

class ImageSourceForm(ModelForm):

    class Meta:
        model = Source
        exclude = (
            'key1', 'key2', 'key3', 'key4', 'key5',    # Handled by a separate form
            'default_point_generation_method',    # Handled by a separate form
            'labelset',    # Handled by the new/edit labelset page
            'image_annotation_area',    # Handled by a separate form
            'enable_robot_classifier',    # Changeable only upon request
        )
        widgets = {
            'image_height_in_cm': TextInput(attrs={'size': 3}),
            'longitude': TextInput(attrs={'size': 10}),
            'latitude': TextInput(attrs={'size': 10}),
        }

    #error_css_class = ...
    #required_css_class = ...

    def __init__(self, *args, **kwargs):

        super(ImageSourceForm, self).__init__(*args, **kwargs)

        # This is used to make longitude and latitude required
        self.fields['longitude'].required = True
        self.fields['latitude'].required = True

        # For use in templates.  Can iterate over fieldsets instead of the entire form.
        self.fieldsets = {'general_info': [self[name] for name in ['name', 'visibility', 'description']],
                          'image_height_in_cm': [self[name] for name in ['image_height_in_cm']],
                          'world_location': [self[name] for name in ['latitude', 'longitude']]}


    def clean_annotation_area_percentages(self):
        data = self.cleaned_data

        if 'annotation_min_x' in data and \
           'annotation_max_x' in data and \
           data['annotation_min_x'] > data['annotation_max_x']:

            msg = "The maximum x must be greater than or equal to the minimum x."
            self._errors['annotation_max_x'] = self.error_class([msg])
            del data['annotation_min_x']
            del data['annotation_max_x']

        if 'annotation_min_y' in data and \
           'annotation_max_y' in data and \
           data['annotation_min_y'] > data['annotation_max_y']:

            msg = "The maximum y must be greater than or equal to the minimum y."
            self._errors['annotation_max_y'] = self.error_class([msg])
            del data['annotation_min_y']
            del data['annotation_max_y']

        self.cleaned_data = data

    def clean(self):
        """
        1. Strip spaces from character fields.
        2. Call the parent's clean() to run the default behavior.
        3. Default return behavior of clean() is to return self.cleaned_data.
        """
        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        self.cleaned_data = data

        return super(ImageSourceForm, self).clean()
"""
    def clean_latitude(self):
        latitude = self.cleaned_data['latitude']
        if latitude < -90 or latitude > 90:
            raise ValidationError("Latitude is out of range.")

    def clean_longitude(self):
        longitude = self.cleaned_data['longitude']
        if longitude < -180 or longitude > 180:
            raise ValidationError("Longitude is out of range.")
"""



class LocationKeyForm(Form):
    """
    Location key form for the New Source page.
    """

    class Media:
        js = (
            "js/LocationKeyFormHelper.js",
        )

    def __init__(self, *args, **kwargs):

        super(LocationKeyForm, self).__init__(*args, **kwargs)

        key_field_list = ['key1', 'key2', 'key3', 'key4', 'key5']
        field_labels = dict(
            key1="Key 1",
            key2="Key 2",
            key3="Key 3",
            key4="Key 4",
            key5="Key 5",
        )

        # Create fields: key1, key2, key3, key4, and key5.
        for key_field in key_field_list:

            self.fields[key_field] = fields.CharField(
                label=field_labels[key_field],
                max_length=Source._meta.get_field(key_field).max_length,
                required=not Source._meta.get_field(key_field).blank,
                error_messages=dict(required=str_consts.SOURCE_ONE_KEY_REQUIRED_ERROR_STR),
            )

    def clean(self):
        """
        1. Strip spaces from character fields.
        2. Location key processing: keep key n only if 1 through n-1
        are also specified.
        3. Call the parent's clean() to run the default behavior.
        4. Clean the annotation-area fields.
        5. Default return behavior of clean() is to return self.cleaned_data.
        """
        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        if 'key1' not in data or data['key1'] == u'':
            data['key2'] = u''
        if data['key2'] == u'':
            data['key3'] = u''
        if data['key3'] == u'':
            data['key4'] = u''
        if data['key4'] == u'':
            data['key5'] = u''

        self.cleaned_data = data

        return super(LocationKeyForm, self).clean()


class LocationKeyEditForm(Form):
    """
    Location key form for the Edit Source page.
    """

    def __init__(self, *args, **kwargs):

        source_id = kwargs.pop('source_id')
        super(LocationKeyEditForm, self).__init__(*args, **kwargs)

        source = Source.objects.get(pk=source_id)

        num_of_keys = len(source.get_key_list())
        key_field_list = ['key1', 'key2', 'key3', 'key4', 'key5'][:num_of_keys]
        field_labels = dict(
            key1="Key 1",
            key2="Key 2",
            key3="Key 3",
            key4="Key 4",
            key5="Key 5",
        )

        for key_field in key_field_list:

            self.fields[key_field] = fields.CharField(
                label=field_labels[key_field],
                max_length=Source._meta.get_field(key_field).max_length,
                required=True,
                initial=getattr(source, key_field)
            )

    def clean(self):
        """
        Strip spaces from the fields.
        """
        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        self.cleaned_data = data

        return super(LocationKeyEditForm, self).clean()

class SourceChangePermissionForm(Form):

    perm_change = ChoiceField(label='Permission Level', choices=Source._meta.permissions)

    def __init__(self, *args, **kwargs):
        self.source_id = kwargs.pop('source_id')
        user = kwargs.pop('user')
        super(SourceChangePermissionForm, self).__init__(*args, **kwargs)
        source = Source.objects.get(pk=self.source_id)
        members = source.get_members_ordered_by_role()
        memberList = [(member.id,member.username) for member in members]

        # This removes the current user from users that can have their permission changed
        memberList.remove((user.id,user.username))
        self.fields['user'] = ChoiceField(label='User', choices=[member for member in memberList], required=True)

class SourceRemoveUserForm(Form):

    def __init__(self, *args, **kwargs):
        self.source_id = kwargs.pop('source_id')
        self.user = kwargs.pop('user')
        super(SourceRemoveUserForm, self).__init__(*args, **kwargs)
        source = Source.objects.get(pk=self.source_id)
        members = source.get_members_ordered_by_role()
        memberList = [(member.id,member.username) for member in members]

        # This removes the current user from users that can have their permission changed
        memberList.remove((self.user.id,self.user.username))
        self.fields['user'] = ChoiceField(label='User', choices=[member for member in memberList], required=True)

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


class ImageDetailForm(ModelForm):
    class Meta:
        model = Metadata
        exclude = ('annotation_area',)
        widgets = {
            'height_in_cm': TextInput(attrs={'size': 3}),
            'longitude': TextInput(attrs={'size': 10}),
            'latitude': TextInput(attrs={'size': 10}),
            'depth': TextInput(attrs={'size': 10}),
        }

    class Media:
        js = (
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

        self.form_help_text = Source._meta.get_field('default_point_generation_method').help_text

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


class LabelImportForm(Form):
    labelset_description = CharField(
        label='Labelset description',
    )

    labels_file = FileField(
        label='Labels file (.txt)',
    )
