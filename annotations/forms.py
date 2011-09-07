from itertools import chain
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django import forms
from django.forms.models import ModelForm
from annotations.models import Label, LabelSet

# Custom widget to enable multiple checkboxes without outputting a wrongful
# helptext since I'm modifying the widget used to display labels.
# This is a workaround for a bug in Django which associates helptext
# with the view instead of with the widget being used.
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

class NewLabelSetForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(NewLabelSetForm, self).__init__(*args, **kwargs)
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
