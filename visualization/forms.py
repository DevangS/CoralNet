from django import forms
from django.forms.fields import DateField, ChoiceField, CharField
from django.forms.widgets import TextInput
from django.shortcuts import get_object_or_404
from annotations.models import Label, LabelSet
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata
from django.forms.extras.widgets import SelectDateWidget

DATE_CHOICES = ()

#gSource = get_object_or_404(Source, id=1)

class YearModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, Metadata):
        return Metadata.photo_date.year


class VisualizationSearchForm(forms.Form):
    class Meta:
        fields = ('value1', 'value2', 'value3',
              'value4', 'value5', 'year', 'labels')
        
    def __init__(self,source_id,*args,**kwargs):
        super(VisualizationSearchForm,self).__init__(*args,**kwargs)
        source = Source.objects.filter(id=source_id)[0]
        metadatas = Metadata.objects.filter(image__source=source).distinct().dates('photo_date', 'year')
        years = []
        for metadata in metadatas:
            if metadata:
                if not metadata.year in years:
                    years.append(metadata.year)

        self.fields['year'] = ChoiceField(choices=years,
                                                required=False)

        labelset = LabelSet.objects.filter(source=source)[0]
        self.fields['labels'] = forms.ModelChoiceField(labelset.labels.all(),
                                            empty_label="View Whole Images",
                                            required=False)
        for key, valueField, valueClass in [
                (source.key1, 'value1', Value1),
                (source.key2, 'value2', Value2),
                (source.key3, 'value3', Value3),
                (source.key4, 'value4', Value4),
                (source.key5, 'value5', Value5)
                ]:
            if key:
                choices = [('', 'All')]
                valueObjs = valueClass.objects.filter(source=source).order_by('name')
                for valueObj in valueObjs:
                    choices.append((valueObj.id, valueObj.name))
                
                self.fields[valueField] = ChoiceField(choices, label=key, required=False)
                



           # else:
            #    del self.fields[valueField]

"""        global gSource
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
    labels = forms.ModelChoiceField(queryset=(), empty_label="All", required=False) """
