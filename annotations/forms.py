from itertools import chain
from django.core.urlresolvers import reverse
from django.forms.fields import CharField, BooleanField
from django.forms.widgets import TextInput, HiddenInput
from django.utils import simplejson
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django import forms
from django.forms.models import ModelForm
from accounts.utils import is_robot_user
from annotations.models import Label, LabelSet, Annotation
from CoralNet.forms import FormHelper

# Custom widget to enable multiple checkboxes without outputting a wrongful
# helptext since I'm modifying the widget used to display labels.
# This is a workaround for a bug in Django which associates helptext
# with the view instead of with the widget being used.
from images.models import Point

class CustomCheckboxSelectMultiple(forms.CheckboxSelectMultiple):

   items_per_row = 4 # Number of items per row

   def render(self, name, value, attrs=None, choices=()):
       if value is None: value = []
       has_id = attrs and 'id' in attrs
       final_attrs = self.build_attrs(attrs, name=name)
       output = ['<table><tr>']
       # Normalize to strings
       str_values = set([force_unicode(v) for v in value])
       for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
           # If an ID attribute was given, add a numeric index as a suffix,
           # so that the checkboxes don't all have the same ID attribute.
           if has_id:
               final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
               label_for = ' for="%s"' % final_attrs['id']
           else:
               label_for = ''

           cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
           option_value = force_unicode(option_value)
           rendered_cb = cb.render(name, option_value)
           option_label = conditional_escape(force_unicode(option_label))
           if i != 0 and i % self.items_per_row == 0:
               output.append('</tr><tr>')
           output.append('<td nowrap><label%s>%s %s</label></td>' % (label_for, rendered_cb, option_label))
       output.append('</tr></table>')
       return mark_safe('\n'.join(output))

class NewLabelForm(ModelForm):
    class Meta:
        model = Label
        widgets = {
            'code': TextInput(attrs={'size': 10}),
        }
        
    def clean(self):
        """
        1. Strip spaces from character fields.
        2. Add an error if the specified name or code matches that of an existing label.
        3. Call the parent's clean() to finish up with the default behavior.
        """
        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        if data.has_key('name'):
            labelsOfSameName = Label.objects.filter(name__iexact=data['name'])
            if len(labelsOfSameName) > 0:
                # mark_safe(), along with the |safe template filter, allows HTML in the message.
                msg = mark_safe('There is already a label with the name %s: <a href="%s" target="_blank">%s</a>' % (
                    data['name'],
                    reverse('label_main', args=[labelsOfSameName[0].id]),
                    labelsOfSameName[0].name,
                ))
                self._errors['name'] = self.error_class([msg])

        if data.has_key('code'):
            labelsOfSameCode = Label.objects.filter(code__iexact=data['code'])
            if len(labelsOfSameCode) > 0:
                msg = mark_safe('There is already a label with the short code %s: <a href="%s" target="_blank">%s</a>' % (
                    data['code'],
                    reverse('label_main', args=[labelsOfSameCode[0].id]),
                    labelsOfSameCode[0].name,
                ))
                self._errors['code'] = self.error_class([msg])

        self.cleaned_data = data
        return super(NewLabelForm, self).clean()

class NewLabelSetForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewLabelSetForm, self).__init__(*args, **kwargs)

        # Put the label choices in order
        self.fields['labels'].choices = \
            [(label.id, label) for label in Label.objects.all().order_by('group__id', 'name')]

        # Custom widget for label selection
        self.fields['labels'].widget = CustomCheckboxSelectMultiple(
            choices=self.fields['labels'].choices)
        # Removing "Hold down "Control", or "Command" on a Mac, to select more than one."
        self.fields['labels'].help_text = ''

    class Meta:
        model = LabelSet

        # description and location are obsolete now that there's a 1-to-1
        # correspondence between labelsets and sources.
        exclude = ('description', 'location')

    class Media:
        js = (
            # From this app's static folder
            "js/LabelsetFormHelper.js",
        )


class AnnotationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        image = kwargs.pop('image')
        user = kwargs.pop('user')
        super(AnnotationForm, self).__init__(*args, **kwargs)

        self.fields['image_id'] = CharField(
            widget=HiddenInput(),
            initial=str(image.id),
        )
        self.fields['user_id'] = CharField(
            widget=HiddenInput(),
            initial=str(user.id),
        )

        labelFieldMaxLength = Label._meta.get_field('code').max_length


        for point in Point.objects.filter(image=image).order_by('point_number'):

            try:
                existingAnnotation = Annotation.objects.get(point=point)
            except Annotation.DoesNotExist:
                existingAnnotation = None

            if existingAnnotation:
                existingAnnoCode = existingAnnotation.label.code
                isRobotAnnotation = is_robot_user(existingAnnotation.user)
            else:
                existingAnnoCode = ''
                isRobotAnnotation = None

            pointNum = point.point_number

            # Create the text field for annotating a point with a label code.
            # label_1 for point 1, label_23 for point 23, etc.
            labelFieldName = 'label_' + str(pointNum)

            self.fields[labelFieldName] = CharField(
                widget=TextInput(attrs=dict(
                    size=6,
                )),
                max_length=labelFieldMaxLength,
                label=str(pointNum),
                required=False,
                initial=existingAnnoCode,
            )

            # Create a hidden field to indicate whether a point is robot-annotated or not.
            # robot_1 for point 1, robot_23 for point 23, etc.
            robotFieldName = 'robot_' + str(pointNum)

            self.fields[robotFieldName] = BooleanField(
                widget=HiddenInput(),
                required=False,
                initial=simplejson.dumps(isRobotAnnotation),
            )
