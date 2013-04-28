from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from images.models import Point, Image, Source, Robot
from userena.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from CoralNet.utils import generate_random_filename

def get_label_thumbnail_upload_path(instance, filename):
    """
    Generate a destination path (on the server filesystem) for
    an upload of a label's representative thumbnail image.
    """
    return generate_random_filename(settings.LABEL_THUMBNAIL_DIR, filename, numOfChars=10)


class LabelGroupManager(models.Manager):
    def get_by_natural_key(self, code):
        """
        Allow fixtures to refer to Label Groups by short code instead of by id.
        """
        return self.get(code=code)

class LabelGroup(models.Model):
    objects = LabelGroupManager()

    name = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=10, blank=True)

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name


class LabelManager(models.Manager):
    def get_by_natural_key(self, code):
        """
        Allow fixtures to refer to Labels by short code instead of by id.
        """
        return self.get(code=code)

class Label(models.Model):
    objects = LabelManager()

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

        if self.isEmptyLabelset():
            # Empty labelset
            return "Empty labelset"

        try:
            source = Source.objects.get(labelset=self)
            # Labelset of a source
            return "%s labelset" % source
        except Source.DoesNotExist:
            # Labelset that's not in any source (perhaps a really old
            # labelset from early site development)
            return "(Labelset not used in any source) " + self.description

    
class Annotation(models.Model):
    annotation_date = models.DateTimeField(blank=True, auto_now=True, editable=False)
    point = models.ForeignKey(Point, editable=False)
    image = models.ForeignKey(Image, editable=False)

    # The user who made this annotation
    user = models.ForeignKey(User, editable=False)
    # Only fill this in if the user is the robot user
    robot_version = models.ForeignKey(Robot, editable=False, null=True)

    label = models.ForeignKey(Label) #TODO: verify
    source = models.ForeignKey(Source, editable=False)

    def __unicode__(self):
        return "%s - %s - %s" % (self.image, self.point.point_number, self.label.code)


class AnnotationToolAccess(models.Model):
    access_date = models.DateTimeField(blank=True, auto_now=True, editable=False)
    image = models.ForeignKey(Image, editable=False)
    source = models.ForeignKey(Source, editable=False)
    user = models.ForeignKey(User, editable=False)


class AnnotationToolSettings(models.Model):

    user = models.ForeignKey(User, editable=False)

    POINT_MARKER_CHOICES = (
        ('crosshair', 'Crosshair'),
        ('circle', 'Circle'),
        ('crosshair and circle', 'Crosshair and circle'),
        ('box', 'Box'),
        )
    MIN_POINT_MARKER_SIZE = 1
    MAX_POINT_MARKER_SIZE = 30
    MIN_POINT_NUMBER_SIZE = 1
    MAX_POINT_NUMBER_SIZE = 40

    point_marker = models.CharField(max_length=30, choices=POINT_MARKER_CHOICES, default='crosshair')
    point_marker_size = models.IntegerField(
        default=16,
        validators=[
            MinValueValidator(MIN_POINT_MARKER_SIZE),
            MaxValueValidator(MAX_POINT_MARKER_SIZE),
        ],
    )
    point_marker_is_scaled = models.BooleanField(default=False)

    point_number_size = models.IntegerField(
        default=24,
        validators=[
            MinValueValidator(MIN_POINT_NUMBER_SIZE),
            MaxValueValidator(MAX_POINT_NUMBER_SIZE),
        ],
    )
    point_number_is_scaled = models.BooleanField(default=False)

    unannotated_point_color = models.CharField(max_length=6, default='FFFF00')
    robot_annotated_point_color = models.CharField(max_length=6, default='FFFF00')
    human_annotated_point_color = models.CharField(max_length=6, default='8888FF')
    selected_point_color = models.CharField(max_length=6, default='00FF00')

    show_machine_annotations = models.BooleanField(default=True)