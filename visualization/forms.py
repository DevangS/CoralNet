from django import forms
from django.shortcuts import get_object_or_404
from images.models import Source, Value1, Value2, Value3, Value4, Value5
from django.contrib.auth.models import User

class VisualizationSearchForm(forms.Form):
    def __init__(self,source_id,*args,**kwargs):
        super(VisualizationSearchForm,self).__init__(*args,**kwargs)
        source = get_object_or_404(Source,id=source_id)
        self.fields['value1s'] = forms.ModelChoiceField(queryset=Value1.objects.filter(source=source))
        self.fields['value2s'] = forms.ModelChoiceField(queryset=Value2.objects.filter(source=source))
        self.fields['value3s'] = forms.ModelChoiceField(queryset=Value3.objects.filter(source=source))
        self.fields['value4s'] = forms.ModelChoiceField(queryset=Value4.objects.filter(source=source))
        self.fields['value5s'] = forms.ModelChoiceField(queryset=Value5.objects.filter(source=source))
   
