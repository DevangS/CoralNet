from django import forms
from images.models import Source, Value
from django.contrib.auth.models import User

class SourceSelectionForm(forms.Form):
    visible_sources = [source for source in Source.objects.all()
                       if source.visible_to_user(user) ]
    form = forms.ModelChoiceField(queryset=visible_sources, empty_label="")

class VisualizationSearchForm(forms.Form):
    values1 = forms.ModelChoiceField(queryset=Value.objects.filter(source=Source_id))
    images = forms.ModelChoiceField(queryset=)
