from django.forms import ModelForm
from bug_reporting.models import Feedback
from CoralNet.forms import FormHelper

class FeedbackForm(ModelForm):
    class Meta:
        model = Feedback
        fields = ('type', 'comment')    # Other fields are auto-set

    #error_css_class = ...
    #required_css_class = ...

    def clean(self):
        """
        1. Strip spaces from character fields.
        2. Call the parent's clean() to finish up with the default behavior.
        """

        data = FormHelper.stripSpacesFromFields(
            self.cleaned_data, self.fields)

        self.cleaned_data = data

        return super(FeedbackForm, self).clean()