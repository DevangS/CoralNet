from django.db import models
from images.models import Point, Image, Source
from userena.models import User

class LabelGroup(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=10, blank=True)

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name

class Label(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=10, blank=True)
    group = models.ForeignKey(LabelGroup)
    
    def __unicode__(self):
        """
        To-string method.
        """
        return self.name

class LabelSet(models.Model):
    description = models.TextField(blank=True)
    location = models.CharField(max_length=45, blank=True)
    labels = models.ManyToManyField(Label)
    edit_date = models.DateTimeField('Date edited', auto_now=True, editable=False)

    # Since null-or-non-null foreign keys can be a pain,
    # here's a dummy labelset object...
    EMPTY_LABELSET_ID = -1

    @staticmethod
    def getEmptyLabelset():
        return LabelSet.objects.get(pk=LabelSet.EMPTY_LABELSET_ID)

    def isEmptyLabelset(self):
        return self.pk == LabelSet.EMPTY_LABELSET_ID

    def __unicode__(self):
        try:
            source = Source.objects.get(labelset=self)
            return "%s labelset" % source
        except Source.DoesNotExist:
            return "(Labelset not used in any source) " + self.description

    
class Annotation(models.Model):
    annotation_date = models.DateTimeField(blank=True, auto_now=True, editable=False)
    point = models.ForeignKey(Point)
    image = models.ForeignKey(Image)
    # 'user' can be the dummy user "Imported".
    user = models.ForeignKey(User)
    label = models.ForeignKey(Label) #TODO: verify
    source = models.ForeignKey(Source)