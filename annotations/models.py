from django.db import models
import accounts
import images

class annotation_attempt(models.Model):
    description = models.TextField(blank=True)
    source = models.ForeignKey(images.models.Source)
    user = models.ForeignKey(accounts.models.Profile)

class Label(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=5, blank=True)
    group = models.ForeignKey(LabelGroup)

class LabelSet(models.Model):
    description = models.TextField(blank=True)
    location = models.CharField(max_length=45, blank=True)
    attempt = models.ForeignKey(annotation_attempt)
    
class LabelGroup(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=5, blank=True)

class Annotation(models.Model):
    annotation_date = models.DateField()
    point = models.ForeignKey(images.models.Point)
    image = models.ForeignKey(images.models.Image)
    user = models.ForeignKey(accounts.models.Profile)
    label = models.ForeignKey(Label) #TODO: verify
    attempt = models.ForeignKey(annotation_attempt)