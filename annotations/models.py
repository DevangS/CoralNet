from django.conf import settings
from django.db import models
from images.models import Point, Image, Source
from userena.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from CoralNet.utils import generate_random_filename

def get_label_thumbnail_upload_path(instance, filename):
    """
    Generate a destination path (on the server filesystem) for
    an upload of a label's representative thumbnail image.
    """
    return generate_random_filename(settings.LABEL_THUMBNAIL_DIR, filename, numOfChars=10)

class LabelGroup(models.Model):
    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=10, blank=True)

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name

class Label(models.Model):
    name = models.CharField(max_length=45)
    code = models.CharField('Short Code', max_length=10)
    group = models.ForeignKey(LabelGroup, verbose_name='Functional Group')
    description = models.TextField(null=True)
    
    # easy_thumbnails reference: http://packages.python.org/easy-thumbnails/ref/processors.html
    THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT = 150, 150
    thumbnail = ThumbnailerImageField(
        'Example image (thumbnail)',
        upload_to=get_label_thumbnail_upload_path,
        resize_source=dict(size=(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), crop='smart'),
        help_text="For best results, please use an image that's close to %d x %d pixels.\n" % (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT) + \
                  "Otherwise, we'll resize and crop your image to make sure it's that size.",
        null=True
    )
    
    create_date = models.DateTimeField('Date created', auto_now_add=True, editable=False, null=True)
    created_by = models.ForeignKey(User, verbose_name='Created by', editable=False, null=True)
    
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
    point = models.ForeignKey(Point, editable=False)
    image = models.ForeignKey(Image, editable=False)
    # 'user' can be the dummy user "Imported".
    user = models.ForeignKey(User)
    label = models.ForeignKey(Label) #TODO: verify
    source = models.ForeignKey(Source, editable=False)

    def __unicode__(self):
        return "%s - %s - %s" % (self.image, self.point.point_number, self.label.code)