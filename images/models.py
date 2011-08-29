import random
import string
from os.path import splitext

import settings
from django.db import models

from django.contrib.auth.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from guardian.shortcuts import get_objects_for_user, get_perms

class Source(models.Model):

    # Example: 'Moorea'
    name = models.CharField(max_length=200, unique=True)

    VISIBILITY_CHOICES = (
        ('b', "Public"),    # Eventually, public Sources could still have individual images be public/private
        ('v', "Private"),
    )
    visibility = models.CharField(max_length=1, choices=VISIBILITY_CHOICES, default='v')

    # Automatically set to the date and time of creation.
    create_date = models.DateTimeField('Date created', auto_now_add=True, editable=False)

    description = models.TextField(blank=True)

    labelset = models.ForeignKey('annotations.LabelSet')
    
    # Each of these fields is allowed to be blank (an empty string).
    # We're assuming that we'll only have key 2 if we have
    # key 1, we'll only have key 3 if we have key 2, etc.
    key1 = models.CharField('Key 1', max_length=50, blank=True, help_text='Location keys - 1 most general, 5 most specific')
    key2 = models.CharField('Key 2', max_length=50, blank=True)
    key3 = models.CharField('Key 3', max_length=50, blank=True)
    key4 = models.CharField('Key 4', max_length=50, blank=True)
    key5 = models.CharField('Key 5', max_length=50, blank=True)

    default_total_points = models.IntegerField('Annotation points per image')

    longitude = models.CharField(max_length=20, blank=True, help_text='World location - for locating your Source on Google Maps')
    latitude = models.CharField(max_length=20, blank=True)

    # Permissions for users to perform actions on Sources
    class Meta:
        permissions = (
            ('source_admin', 'Admin'),
        )

    ##########
    # Database-query methods related to Sources
    ##########
    @staticmethod
    def get_public_sources():
        return [source for source in Source.objects.all()
                if source.visibility == 'b']

    @staticmethod
    def get_sources_of_user(user):
        return get_objects_for_user(user, 'images.source_admin')

    #TODO: There's probably a way to optimize this, as well as any code
    # that uses both get_sources_of_user and get_other_public_sources
    @staticmethod
    def get_other_public_sources(user):
        return [source for source in Source.objects.all()
                if (source.visibility == 'b' and source not in Source.get_sources_of_user(user))]

    #TODO: get rid of the 'user.is_superuser' hack.  That's just to prevent superusers from
    #appearing in every single Source's member list, but it also prevents superusers from
    #using Sources at all.
    def has_member(self, user):
        return (get_perms(user, self) != []) and not user.is_superuser

    def get_members(self):
        return [user for user in User.objects.all()
                if self.has_member(user) ]

    def visible_to_user(self, user):
        return (self.visibility == 'b') or self.has_member(user)

    def get_all_images(self):
        return Image.objects.filter(source=self)

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name


class LocationValue(models.Model):
    class Meta:
        # An abstract base class; no table will be created for
        # this class, but tables will be created for its sub-classes
        abstract = True

    name = models.CharField(max_length=50)
    source = models.ForeignKey(Source)

    def __unicode__(self):
        return self.name

class Value1(LocationValue):
    pass
class Value2(LocationValue):
    pass
class Value3(LocationValue):
    pass
class Value4(LocationValue):
    pass
class Value5(LocationValue):
    pass

class Metadata(models.Model):
    name = models.CharField(max_length=200, blank=True)
    photo_date = models.DateField('Photo date')
    description = models.TextField(max_length=1000, blank=True)
    # Do we need any input checking on pixel_cm_ratio?
    pixel_cm_ratio = models.CharField('Pixel/cm ratio', max_length=45, null=True, blank=True)
    camera = models.CharField(max_length=200, blank=True)
    strobes = models.CharField(max_length=200, blank=True)
    photographer = models.CharField(max_length=45, blank=True)
    water_quality = models.CharField(max_length=45, blank=True)
    value1 = models.ForeignKey(Value1, null=True, blank=True)
    value2 = models.ForeignKey(Value2, null=True, blank=True)
    value3 = models.ForeignKey(Value3, null=True, blank=True)
    value4 = models.ForeignKey(Value4, null=True, blank=True)
    value5 = models.ForeignKey(Value5, null=True, blank=True)
    group1_percent = models.IntegerField(default=0)
    group2_percent = models.IntegerField(default=0)
    group3_percent = models.IntegerField(default=0)
    group4_percent = models.IntegerField(default=0)
    group5_percent = models.IntegerField(default=0)
    group6_percent = models.IntegerField(default=0)
    group7_percent = models.IntegerField(default=0)

    def __unicode__(self):
        return "Metadata of " + self.name


def rand_string():
    """
    Generates a 10-char-long string of lowercase letters and numbers.
    That makes 36^10 = 3 x 10^15 possibilities.
    
    If we generate filenames randomly, it's harder for people to guess filenames
    and view images when they don't have permission to do so.
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(10))

def generate_image_filename(originalFilename):
    #TODO: Check for filename collisions with existing files

    extension = splitext(originalFilename)[1]
    filenameBase = rand_string()
    return filenameBase + extension

def get_original_image_upload_path(instance, filename):
    """
    Generate a destination path (on the server filesystem) for
    a data-image upload. This will be automatically prepended
    with MEDIA_ROOT.
    """
    return settings.ORIGINAL_IMAGE_DIR + generate_image_filename(filename)
    
class Image(models.Model):
    # width_field and height_field allow Django to cache the width and height values
    # so that the image file doesn't have to be read every time we want the width and height.
    # The cache is only updated when the image is saved.
    original_file = ThumbnailerImageField(
        upload_to=get_original_image_upload_path,
        width_field="original_width", height_field="original_height")

    # Cached width and height values for the file field.
    original_width = models.IntegerField()
    original_height = models.IntegerField()

    #TODO: Add another field for the processed image file.
    # Also add the corresponding width/height fields if we allow image cropping or resizing.

    upload_date = models.DateTimeField('Upload date', auto_now_add=True, editable=False)
    uploaded_by = models.ForeignKey(User, editable=False)
    status = models.CharField(max_length=1, blank=True)
    total_points = models.IntegerField('Number of annotation points')
    metadata = models.ForeignKey(Metadata)
    source = models.ForeignKey(Source)

    def __unicode__(self):
        return self.metadata.name

    # Use this as the "title" element of the image on an HTML page
    # (hover the mouse over the image to see this)
    def get_image_element_title(self):
        metadata = self.metadata
        dataStrings = []
        for v in [metadata.value1,
                  metadata.value2,
                  metadata.value3,
                  metadata.value4,
                  metadata.value5 ]:
            if v:
                dataStrings.append(v.name)
            else:
                break
        if metadata.photo_date:
            dataStrings.append(str(metadata.photo_date))

        return ' '.join(dataStrings)

class Point(models.Model):
    row = models.IntegerField()
    column = models.IntegerField()
    point_number = models.IntegerField()
    annotation_status = models.CharField(max_length=1, blank=True)
    image = models.ForeignKey(Image)
