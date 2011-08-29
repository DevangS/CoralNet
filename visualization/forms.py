from django import forms
from django.forms.fields import DateField
from django.shortcuts import get_object_or_404
from annotations.models import Label
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata
from django.forms.extras.widgets import SelectDateWidget

MODE_CHOICES = (
    ('image', 'View whole images'),
    ('patch', 'View patches'),
)

DATE_CHOICES = ()

gSource = get_object_or_404(Source, id=1)

class YearModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, Metadata):
        return Metadata.photo_date.year


class VisualizationSearchForm(forms.Form):

    def __init__(self,source_id,*args,**kwargs):
        super(VisualizationSearchForm,self).__init__(*args,**kwargs)
        global gSource
        gSource = get_object_or_404(Source,id=source_id)

        #Gets options to show for each value that the user selects
        if gSource.key1:
            self.fields[gSource.key1].queryset = Value1.objects.filter(source=gSource)
        if gSource.key2:
            self.fields[gSource.key2].queryset = Value2.objects.filter(source=gSource)
        if gSource.key3:
            self.fields[gSource.key3].queryset = Value3.objects.filter(source=gSource)
        if gSource.key4:
            self.fields[gSource.key4].queryset = Value4.objects.filter(source=gSource)
        if gSource.key5:
            self.fields[gSource.key5].queryset = Value5.objects.filter(source=gSource)
        self.fields['year'].queryset = Metadata.objects.filter(image__source=gSource).distinct()
        self.fields['labels'].queryset = Label.objects.filter(labelset__id=gSource.labelset_id).distinct()

    global gSource
    
    #These checks are redundant with the field ones above, but after spending 2 hours on this issue,
    # it's the best I came up with and there's a deadline to meet so TODO: optimize by trying to use get method on vars()
    if gSource.key1:
        vars()[gSource.key1] = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    if gSource.key2:
        vars()[gSource.key2] = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    if gSource.key3:
        vars()[gSource.key3] = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    if gSource.key4:
        vars()[gSource.key4] = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
    if gSource.key5:
        vars()[gSource.key5] = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
        
    year = YearModelChoiceField(queryset=(), empty_label="All", required=False)
    mode = forms.ChoiceField(choices=MODE_CHOICES)
    labels = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
