from django import forms
from django.forms.fields import ChoiceField, CharField
from django.forms.widgets import HiddenInput
from annotations.models import LabelSet
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata

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

        self.fields['year'] = ChoiceField(choices=[('',"All")] + [(year,year) for year in years],
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


class ImageBatchActionForm(forms.Form):
    action = ChoiceField(
        label="Action",
        choices=(
            ('', '---------'),
            ('delete', 'Delete'),
        ),
        error_messages = {
            'required': 'No action selected.',
        }
    )

    # The search keys as a JSON-ized dictionary
    searchKeys = CharField(widget=HiddenInput())
