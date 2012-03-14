from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from django.contrib.auth.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from guardian.shortcuts import get_objects_for_user, get_users_with_perms, get_perms, assign
from images.model_utils import PointGen, AnnotationAreaUtils
from CoralNet.utils import generate_random_filename

# Constants that don't really belong to a particular model
class ImageModelConstants():
    MIN_IMAGE_CM_HEIGHT = 1
    MAX_IMAGE_CM_HEIGHT = 100000


class Source(models.Model):

    class VisibilityTypes():
        PUBLIC = 'b'
        PUBLIC_VERBOSE = 'Public'
        PRIVATE = 'v'
        PRIVATE_VERBOSE = 'Private'

    # Example: 'Moorea'
    name = models.CharField(max_length=200, unique=True)

    VISIBILITY_CHOICES = (
        (VisibilityTypes.PUBLIC, VisibilityTypes.PUBLIC_VERBOSE),
        (VisibilityTypes.PRIVATE, VisibilityTypes.PRIVATE_VERBOSE),
    )
    visibility = models.CharField(max_length=1, choices=VISIBILITY_CHOICES, default=VisibilityTypes.PRIVATE)

    # Automatically set to the date and time of creation.
    create_date = models.DateTimeField('Date created', auto_now_add=True, editable=False)

    description = models.TextField(blank=True)

    labelset = models.ForeignKey('annotations.LabelSet')
    
    # Each of these fields is allowed to be blank (an empty string).
    # We're assuming that we'll only have key 2 if we have
    # key 1, we'll only have key 3 if we have key 2, etc.
    key1 = models.CharField('Key 1', max_length=50, blank=True)
    key2 = models.CharField('Key 2', max_length=50, blank=True)
    key3 = models.CharField('Key 3', max_length=50, blank=True)
    key4 = models.CharField('Key 4', max_length=50, blank=True)
    key5 = models.CharField('Key 5', max_length=50, blank=True)

    POINT_GENERATION_CHOICES = (
        (PointGen.Types.SIMPLE, PointGen.Types.SIMPLE_VERBOSE),
        (PointGen.Types.STRATIFIED, PointGen.Types.STRATIFIED_VERBOSE),
        (PointGen.Types.UNIFORM, PointGen.Types.UNIFORM_VERBOSE),
    )
    default_point_generation_method = models.CharField(
        "Point generation method",
        help_text="When we create annotation points for uploaded images, this is how we'll generate the point locations.",
        max_length=50,
        default=PointGen.args_to_db_format(
                    point_generation_type=PointGen.Types.SIMPLE,
                    simple_number_of_points=200)
    )

    image_height_in_cm = models.IntegerField(
        "Default image height coverage (centimeters)",
        help_text="The automatic annotation system needs to know how much space is covered by each image.\n"
                  "You can also set this on a per-image basis; for images that don't have a specific value set, this default value will be used.",
        validators=[MinValueValidator(ImageModelConstants.MIN_IMAGE_CM_HEIGHT),
                    MaxValueValidator(ImageModelConstants.MAX_IMAGE_CM_HEIGHT)],
        null=True
    )

    image_annotation_area = models.CharField(
        "Default image annotation area",
        help_text="This defines a rectangle of the image where annotation points are allowed to be generated.\n"
                  "For example, X boundaries of 10% and 95% mean that the leftmost 10% and the rightmost 5% of the image will not have any points.\n"
                  "You can also set these boundaries as pixel counts on a per-image basis; for images that don't have a specific value set, these percentages will be used.",
        max_length=50,
        null=True
    )

    longitude = models.CharField(max_length=20, blank=True)
    latitude = models.CharField(max_length=20, blank=True)

    #start_date = models.DateField(null=True, blank=True)
    #end_date = models.DateField(null=True, blank=True)

    class Meta:
        # Permissions for users to perform actions on Sources.
        # (Unfortunately, inner classes can't use outer-class
        # variables such as constants... so we've hardcoded these.)
        permissions = (
            ('source_view', 'View'),
            ('source_edit', 'Edit'),
            ('source_admin', 'Admin'),
        )

    class PermTypes:
        class ADMIN():
            code = 'source_admin'
            fullCode  = 'images.' + code
            verbose = 'Admin'
        class EDIT():
            code = 'source_edit'
            fullCode  = 'images.' + code
            verbose = 'Edit'
        class VIEW():
            code = 'source_view'
            fullCode  = 'images.' + code
            verbose = 'View'

    ##########
    # Helper methods for sources
    ##########
    @staticmethod
    def get_public_sources():
        return Source.objects.filter(visibility=Source.VisibilityTypes.PUBLIC).order_by('name')

    @staticmethod
    def get_sources_of_user(user):
        # For superusers, this returns ALL sources.
        if user.is_authenticated():
            return get_objects_for_user(user, Source.PermTypes.VIEW.fullCode).order_by('name')
        else:
            return []

    @staticmethod
    def get_other_public_sources(user):
        return [source for source in Source.get_public_sources()
                if source not in Source.get_sources_of_user(user)]

    def has_member(self, user):
        return user in self.get_members()

    def get_members(self):
        return get_users_with_perms(self).order_by('username')

    def get_member_role(self, user):
        """
        Get a user's conceptual "role" in the source.

        If they have admin perms, their role is admin.
        Otherwise, if they have edit perms, their role is edit.
        Otherwise, if they have view perms, their role is view.
        Role is None if user is not a Source member.
        """
        perms = get_perms(user, self)

        for permType in [Source.PermTypes.ADMIN,
                         Source.PermTypes.EDIT,
                         Source.PermTypes.VIEW]:
            if permType.code in perms:
                return permType.verbose

    @staticmethod
    def _member_sort_key(memberAndRole):
        role = memberAndRole[1]
        if role == Source.PermTypes.ADMIN.verbose:
            return 1
        elif role == Source.PermTypes.EDIT.verbose:
            return 2
        elif role == Source.PermTypes.VIEW.verbose:
            return 3

    def get_members_ordered_by_role(self):
        """
        Admin first, then edit, then view.

        Within a role, members are sorted by username.  This is
        because get_members() orders members by username, and Python
        sorts are stable (meaning that when multiple records have
        the same key, their original order is preserved).
        """

        members = self.get_members()
        membersAndRoles = [(m, self.get_member_role(m)) for m in members]
        membersAndRoles.sort(key=Source._member_sort_key)
        orderedMembers = [mr[0] for mr in membersAndRoles]
        return orderedMembers

    def assign_role(self, user, role):
        """
        Shortcut method to assign a conceptual "role" to a user,
        so assigning permissions can be done compactly.

        Admin role: admin, edit, view perms
        Edit role: edit, view perms
        View role: view perm
        """

        if role == Source.PermTypes.ADMIN.code:
            assign(Source.PermTypes.ADMIN.code, user, self)
            assign(Source.PermTypes.EDIT.code, user, self)
            assign(Source.PermTypes.VIEW.code, user, self)
        elif role == Source.PermTypes.EDIT.code:
            assign(Source.PermTypes.EDIT.code, user, self)
            assign(Source.PermTypes.VIEW.code, user, self)
        elif role == Source.PermTypes.VIEW.code:
            assign(Source.PermTypes.VIEW.code, user, self)
        else:
            raise ValueError("Invalid Source role: %s" % role)


    def visible_to_user(self, user):
        return (self.visibility == Source.VisibilityTypes.PUBLIC) or \
               user.has_perm(Source.PermTypes.VIEW.code, self)

    def get_all_images(self):
        return Image.objects.filter(source=self)
    
    def get_key_list(self):
        """
        Get a list of this Source's location keys.
        Just to be safe, only gets key n if keys 1 to n-1 are present.
        """

        keyList = []

        for k in ['key1', 'key2', 'key3', 'key4', 'key5']:
            if getattr(self,k):
                keyList.append(getattr(self,k))
            else:
                break

        return keyList

    def get_value_field_list(self):
        """
        If the source has 3 keys, this returns
        ['value1','value2','value3']
        Could be useful for forms when determining
        which metadata values apply to a given source.
        """
        valueFieldList = []
        
        for k,v in [('key1','value1'),
                    ('key2','value2'),
                    ('key3','value3'),
                    ('key4','value4'),
                    ('key5','value5'),]:
            if getattr(self,k):
                valueFieldList.append(v)

        return valueFieldList

    def num_of_keys(self):
        """
        Return the number of location keys that this Source has.
        """
        return len(self.get_key_list())

    def image_annotation_area_display(self):
        """
        Display the annotation-area parameters in templates.
        Usage: {{ mysource.annotation_area_display }}
        """
        return AnnotationAreaUtils.percentage_string_to_readable_format(self.image_annotation_area)

    def point_gen_method_display(self):
        """
        Display the point generation method in templates.
        Usage: {{ mysource.point_gen_method_display }}
        """
        return PointGen.db_to_readable_format(self.default_point_generation_method)

    def get_latest_robot(self):
		"""
		return the latest robot associated with this source.
		if no robots, retun None
		"""
    	# Get all robots for this source
		allRobots = Robot.objects.filter(source = self)
	 
		# if empty, return
		if len(allRobots) == 0:
			return None
	    
		# find the most recent robot
		latestRobot = allRobots[0]
		for thisRobot in allRobots:
			if thisRobot.version > latestRobot.version:
				latestRobot = thisRobot
		return latestRobot

    def __unicode__(self):
        """
        To-string method.
        """
        return self.name

class SourceInvite(models.Model):
    """
    Invites will be deleted once they're accepted.
    """
    sender = models.ForeignKey(User, related_name='invites_sent', editable=False)
    recipient = models.ForeignKey(User, related_name='invites_received')
    source = models.ForeignKey(Source, editable=False)
    source_perm = models.CharField(max_length=50, choices=Source._meta.permissions)

    class Meta:
        # A user can only be invited once to a source.
        unique_together = ['recipient', 'source']

    def source_perm_verbose(self):
        for permType in [Source.PermTypes.ADMIN,
                         Source.PermTypes.EDIT,
                         Source.PermTypes.VIEW]:
            if self.source_perm == permType.code:
                return permType.verbose


class Robot(models.Model):
    # Later, may tie robots to labelsets instead of sources
    source = models.ForeignKey(Source)
    
    version = models.IntegerField(unique=True)
    path_to_model = models.CharField(max_length=500)
    time_to_train = models.BigIntegerField()

    # Automatically set to the date and time of creation.
    create_date = models.DateTimeField('Date created', auto_now_add=True, editable=False)
    
    def get_process_date_short_str(self):
        """
        Return the image's (pre)process date in YYYY-MM-DD format.

        Advantage over YYYY-(M)M-(D)D: alphabetized = sorted by date
        Advantage over YYYY(M)M(D)D: date is unambiguous
        """
        return "{0}-{1:02}-{2:02}".format(self.create_date.year, self.create_date.month, self.create_date.day)


    def __unicode__(self):
        """
        To-string method.
        """
        return "Version %s for %s" % (self.version, self.source.name)


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
    photo_date = models.DateField('Photo date',
                                  help_text='Format: YYYY-MM-DD')

    latitude = models.CharField(max_length=20, blank=True)
    longitude = models.CharField(max_length=20, blank=True)
    depth = models.CharField(max_length=45, blank=True)

    height_in_cm = models.IntegerField(
        "Height covered (centimeters)",
        help_text="The automatic annotation system needs to know how much space is covered by the image.\n"
                  "If you don't set this value, the source's default value will be used.",
        validators=[MinValueValidator(ImageModelConstants.MIN_IMAGE_CM_HEIGHT),
                    MaxValueValidator(ImageModelConstants.MAX_IMAGE_CM_HEIGHT)],
        null=True, blank=True
    )

    annotation_area = models.CharField(
        "Annotation area",
        help_text="This defines a rectangle of the image where annotation points are allowed to be generated.\n"
                  "For example, X boundaries of 150 and 1800 mean that points are only generated within the X-pixel values 150 through 1800.\n"
                  "If you don't set these values, the source's default annotation area (defined with percentages, not pixels) will be used.",
        max_length=50,
        null=True, blank=True
    )
    
    camera = models.CharField(max_length=200, blank=True)
    photographer = models.CharField(max_length=45, blank=True)
    water_quality = models.CharField(max_length=45, blank=True)

    strobes = models.CharField(max_length=200, blank=True)
    framing = models.CharField('Framing gear used', max_length=200, blank=True)
    balance = models.CharField('White balance card', max_length=200, blank=True)
    
    comments = models.TextField(max_length=1000, blank=True)
    
    value1 = models.ForeignKey(Value1, null=True)
    value2 = models.ForeignKey(Value2, null=True)
    value3 = models.ForeignKey(Value3, null=True)
    value4 = models.ForeignKey(Value4, null=True)
    value5 = models.ForeignKey(Value5, null=True)
   # group1_percent = models.IntegerField(default=0)
   # group2_percent = models.IntegerField(default=0)
   # group3_percent = models.IntegerField(default=0)
   # group4_percent = models.IntegerField(default=0)
   # group5_percent = models.IntegerField(default=0)
   # group6_percent = models.IntegerField(default=0)
   # group7_percent = models.IntegerField(default=0)

    def __unicode__(self):
        return "Metadata of " + self.name


class ImageStatus(models.Model):
    preprocessed = models.BooleanField(default=False)
    featuresExtracted = models.BooleanField(default=False)
    hasRandomPoints = models.BooleanField(default=False)
    annotatedByRobot = models.BooleanField(default=False)
    annotatedByHuman = models.BooleanField(default=False)
    featureFileHasHumanLabels = models.BooleanField(default=False)
    usedInCurrentModel = models.BooleanField(default=False)


def get_original_image_upload_path(instance, filename):
    """
    Generate a destination path (on the server filesystem) for
    a data-image upload.
    """
    return generate_random_filename(settings.ORIGINAL_IMAGE_DIR, filename, numOfChars=10)
    
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

    status = models.ForeignKey(ImageStatus, editable=False)

    POINT_GENERATION_CHOICES = (
        (PointGen.Types.SIMPLE, PointGen.Types.SIMPLE_VERBOSE),
        (PointGen.Types.STRATIFIED, PointGen.Types.STRATIFIED_VERBOSE),
        (PointGen.Types.UNIFORM, PointGen.Types.UNIFORM_VERBOSE),
        (PointGen.Types.IMPORTED, PointGen.Types.IMPORTED_VERBOSE),
    )
    point_generation_method = models.CharField(
        'How points were generated',
        max_length=50,
        blank=True,
    )
    
    metadata = models.ForeignKey(Metadata)
    source = models.ForeignKey(Source)

    # To be set by the preprocessing task
    process_date = models.DateTimeField("Date processed", editable=False, null=True)
    # To be set by the classification task
    latest_robot_annotator = models.ForeignKey(Robot, editable=False, null=True)


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

    def get_location_value_str_list(self):
        """
        Returns the image's location values as a list of strings:
        ['Shore3', 'Reef 5', 'Loc10']
        """

        valueList = []
        metadata = self.metadata

        for valueIndex, valueClass in [
                ('value1', Value1),
                ('value2', Value2),
                ('value3', Value3),
                ('value4', Value4),
                ('value5', Value5)
        ]:
            valueObj = getattr(metadata, valueIndex)
            if valueObj:
                valueList.append(valueObj.name)
            else:
                break

        return valueList

    def get_location_values_str(self):
        """
        Returns the image's location values as a single string:
        'Shore3, Reef 5, Loc10'
        """
        return ', '.join(self.get_location_value_str_list())

    def point_gen_method_display(self):
        """
        Display the point generation method in templates.
        Usage: {{ myimage.point_gen_method_display }}
        """
        return PointGen.db_to_readable_format(self.point_generation_method)

    # this function returns the image height by checking both the image and the source for the height
    def height_cm(self):
        thisSource = Source.objects.filter(image = self.id)
        imheight = thisSource[0].image_height_in_cm
        if self.metadata.annotation_area:
            imheight = self.metadata.annotation_area

        return imheight

    def after_height_cm_change(self):
        status = self.status
        status.preprocessed = False
        status.featuresExtracted = False
        status.annotatedByRobot = False
        status.featureFileHasHumanLabels = False
        status.usedInCurrentModel = False
        status.save()

    def annotation_area_display(self):
        """
        Display the annotation area parameters in templates.
        Usage: {{ myimage.annotation_area_display }}
        """
        return AnnotationAreaUtils.annotation_area_string_of_img(self)

    def after_annotation_area_change(self):
        status = self.status
        status.featuresExtracted = False
        status.annotatedByRobot = False
        status.featureFileHasHumanLabels = False
        status.usedInCurrentModel = False
        status.save()

    def after_completed_annotations_change(self):
        """
        Only necessary to run this if human annotations are complete,
        to begin with, and then an annotation is changed.
        """
        status = self.status
        status.featureFileHasHumanLabels = False
        status.usedInCurrentModel = False
        status.save()

    def get_process_date_short_str(self):
        """
        Return the image's (pre)process date in YYYY-MM-DD format.

        Advantage over YYYY-(M)M-(D)D: alphabetized = sorted by date
        Advantage over YYYY(M)M(D)D: date is unambiguous
        """
        return "{0}-{1:02}-{2:02}".format(self.process_date.year, self.process_date.month, self.process_date.day)

class Point(models.Model):
    row = models.IntegerField()
    column = models.IntegerField()
    point_number = models.IntegerField()
    annotation_status = models.CharField(max_length=1, blank=True)
    image = models.ForeignKey(Image)

    def __unicode__(self):
        """
        To-string method.
        """
        return "Point %s" % self.point_number
