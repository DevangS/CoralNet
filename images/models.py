from django.db import models
from guardian.shortcuts import get_objects_for_user, get_perms
from django.contrib.auth.models import User

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

    # Each of these fields is allowed to be blank (an empty string).
    # We're assuming that we'll only have key 2 if we have
    # key 1, we'll only have key 3 if we have key 2, etc.
    key1 = models.CharField('Key 1', max_length=50, blank=True, help_text='Location keys - 1 most general, 5 most specific')
    key2 = models.CharField('Key 2', max_length=50, blank=True)
    key3 = models.CharField('Key 3', max_length=50, blank=True)
    key4 = models.CharField('Key 4', max_length=50, blank=True)
    key5 = models.CharField('Key 5', max_length=50, blank=True)

    longitude = models.CharField(max_length=20, blank=True, help_text='World location - for locating your Source on Google Maps')
    latitude = models.CharField(max_length=20, blank=True)

    # Permissions for users to perform actions on Sources
    class Meta:
        permissions = (
            ('source_admin', 'Admin'),
        )

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

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name

    def detail_str(self):
        """
        Print all the details of this Source.
        This isn't really suitable for __unicode__(), since __unicode__
        would be used for a list of Sources on the admin site...
        but maybe this detail string could still come in handy.
        """
        displayStr = "\nName: " + self.name \
               + "\nVisibility: " + self.get_visibility_display() \
               + "\nDate created: " + str(self.create_date) \
               + "\nDescription: " + self.description
        if self.key1:
            displayStr += ("\nLocation keys: " + self.key1)
        if self.key2:
            displayStr += (", " + self.key2)
        if self.key3:
            displayStr += (", " + self.key3)
        if self.key4:
            displayStr += (", " + self.key4)
        if self.key5:
            displayStr += (", " + self.key5)

        if self.longitude and self.latitude:
            displayStr += ("\nWorld location: Longitude " + self.longitude + ", Latitude " + self.latitude)

        displayStr += "\n"
        return displayStr

class Metadata(models.Model):
    name = models.CharField(max_length=45, blank=True)
    description = models.CharField(max_length=45, blank=True)
    pixel_cm_ratio = models.IntegerField()
    height = models.IntegerField()
    width = models.IntegerField()
    photographer = models.CharField(max_length=45, blank=True)
    water_quality = models.CharField(max_length=45, blank=True)
    group1_percent = models.IntegerField(default=0)
    group2_percent = models.IntegerField(default=0)
    group3_percent = models.IntegerField(default=0)
    group4_percent = models.IntegerField(default=0)
    group5_percent = models.IntegerField(default=0)
    group6_percent = models.IntegerField(default=0)
    group7_percent = models.IntegerField(default=0)

class Image(models.Model):
    status = models.CharField(max_length=1, blank=True)
    total_points = models.IntegerField()
    camera = models.ForeignKey(Metadata)
    source = models.ForeignKey(Source)

class Point(models.Model):
    row = models.IntegerField()
    column = models.IntegerField()
    point_number = models.IntegerField()
    annotation_status = models.CharField(max_length=1, blank=True)
    image = models.ForeignKey(Image)

    #TODO: class value_1, 2, etc?