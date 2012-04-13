from django import forms
from django.forms.fields import ChoiceField, CharField, BooleanField
from django.forms.widgets import HiddenInput
from annotations.forms import CustomCheckboxSelectMultiple
from annotations.models import LabelSet, Label, LabelGroup
from images.models import Source, Value1, Value2, Value3, Value4, Value5, Metadata

class YearModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, Metadata):
        return Metadata.photo_date.year


class VisualizationSearchForm(forms.Form):
    class Meta:
        fields = ('value1', 'value2', 'value3',
              'value4', 'value5', 'year', 'labels', 'image_status', 'annotator')
        
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

        status_choices = [(0, 'All'), (1,'Needs annotation')]
        if source.enable_robot_classifier:
            status_choices.extend([(2, 'Annotated by robot'),(3, 'Annotated by human')])
        else:
            status_choices.append((2, 'Annotated'))
        self.fields['image_status'] = forms.ChoiceField(choices=status_choices,
                                                        required=False)

        self.fields['annotator'] = forms.ChoiceField(choices=[(0,'Human'), (1,'Robot'), (2, 'Both')], required=False)
        
class ImageBatchActionForm(forms.Form):
    class Media:
        js = (
            # From app-specific static directory
            "js/ImageBatchActionFormHelper.js",
        )

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

# Similar to VisualizationSearchForm with the difference that
# label selection appears on a multi-select checkbox form
# TODO: Merge with VisualizationSearchForm to remove redundancy

class StatisticsSearchForm(forms.Form):
    class Meta:
        fields = ('value1', 'value2', 'value3',
              'value4', 'value5', 'labels', 'groups', 'include_robot')

    def __init__(self,source_id,*args,**kwargs):
        super(StatisticsSearchForm,self).__init__(*args,**kwargs)

        # Grab the source and it's labelset
        source = Source.objects.filter(id=source_id)[0]
        labelset = LabelSet.objects.filter(source=source)[0]
        groups = LabelGroup.objects.all().distinct()

        # Get the location keys
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

        #gets all the labels
        labels = labelset.labels.all().order_by('group__id', 'name')

        # Put the label choices in order
        label_choices = \
            [(label.id, label.name) for label in labels]

        group_choices = \
            [(group.id, group.name) for group in groups]
        
        # Custom widget for label selection
        #self.fields['labels'].widget = CustomCheckboxSelectMultiple(choices=self.fields['labels'].choices)
        self.fields['labels']= forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                         choices=label_choices, required=False)

        self.fields['groups']= forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                         choices=group_choices, required=False)
        
        self.fields['include_robot'] = BooleanField(required=False)


