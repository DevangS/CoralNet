from django import forms
from django.forms.fields import DateField
from django.shortcuts import get_object_or_404
from annotations.models import Label, LabelSet
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata
from django.forms.extras.widgets import SelectDateWidget

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
        self.fields['year'].queryset = Metadata.objects.filter(image__source=gSource).distinct() #need to find distinct year
        labelset = LabelSet.objects.filter(source=gSource)[0]
        self.fields['labels'].queryset = labelset.labels.all()

    global gSource

    #These checks are redundant with the field ones above, but after spending 2 hours on this issue,
    # it's the best I came up with and there's a deadline to meet so TODO: optimize
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
    labels = forms.ModelChoiceField(queryset=(), empty_label="All", required=False)
