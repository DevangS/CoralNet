from django.db import models
from CoralNet import accounts
from images.models import Point, Image, Source

class LabelGroup(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=5, blank=True)

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name

class Label(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=5, blank=True)
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
    
class Annotation(models.Model):
    annotation_date = models.DateTimeField(blank=True)
    point = models.ForeignKey(Point)
    image = models.ForeignKey(Image)
    user = models.ForeignKey(accounts.models.Profile)
    label = models.ForeignKey(Label) #TODO: verify
    source = models.ForeignKey(Source)