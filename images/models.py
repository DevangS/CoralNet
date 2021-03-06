import datetime
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from django.contrib.auth.models import User
from easy_thumbnails.fields import ThumbnailerImageField
from guardian.shortcuts import get_objects_for_user, get_users_with_perms, get_perms, assign, remove_perm
from annotations.model_utils import AnnotationAreaUtils
from images.model_utils import PointGen
from CoralNet.utils import generate_random_filename
import os
import json

# Constants that don't really belong to a particular model
class ImageModelConstants():
    MIN_IMAGE_CM_HEIGHT = 1
    MAX_IMAGE_CM_HEIGHT = 100000


class SourceManager(models.Manager):
    def get_by_natural_key(self, name):
        """
        Allow fixtures to refer to Sources by name instead of by id.
        """
        return self.get(name=name)

class Source(models.Model):
    objects = SourceManager()

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

    description = models.TextField()

    affiliation = models.CharField(max_length=200)

    labelset = models.ForeignKey('annotations.LabelSet')
    
    # Each of these fields is allowed to be blank (an empty string).
    # We're assuming that we'll only have key 2 if we have
    # key 1, we'll only have key 3 if we have key 2, etc.
    key1 = models.CharField('Key 1', max_length=50)
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
        help_text="When we create annotation points for uploaded images, this is how we'll generate the point locations. Note that if you change this setting later on, it will NOT apply to images that are already uploaded.",
        max_length=50,
        default=PointGen.args_to_db_format(
                    point_generation_type=PointGen.Types.SIMPLE,
                    simple_number_of_points=200)
    )

    image_height_in_cm = models.IntegerField(
        "Default image height coverage (centimeters)",
        help_text="This is the number of centimeters of substrate the image cover from the top of the image to the bottom. For example, if you use a framer that is 50cm wide and 35cm tall, this value should be set to 35 (or slightly larger if you image covers areas outside the framer). If use you an AUV, you will need to calculate this based on the field of view and distance from the bottom. This information is needed for the automatic annotation system to normalize the pixel to centimeter ratio.\n"
                  "You can also set this on a per-image basis; for images that don't have a specific value set, this default value will be used. Note that all images gets assigned this global default ON UPLOAD. If you change this default, and want this to apply to images that you have already upladed, you must first delete them (under the Browse tab) and then re-upload them.",
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

    alleviate_threshold = models.IntegerField(
        "Level of alleviation (%)",
        validators=[MinValueValidator(0),
                    MaxValueValidator(100)],
        default=0,
    )

    enable_robot_classifier = models.BooleanField(
        "Enable robot classifier",
        default=True,
        help_text="With this option on, the automatic classification system will "
                  "go through your images and add unofficial annotations to them. "
                  "Then when you enter the annotation tool, you will be able to start "
                  "from the system's suggestions instead of from a blank slate.",
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

    def reassign_role(self, user, role):
        """
        Shortcut method that works similarly to assign_role, but removes
        the permissions of the user before reassigning their role. User
        this if the user already has access to a particular source.
        """
        self.remove_role(user)
        self.assign_role(user, role)

    def remove_role(self, user):
        """
        Shortcut method that removes the user from the source.
        """
        remove_perm(Source.PermTypes.ADMIN.code, user, self)
        remove_perm(Source.PermTypes.EDIT.code, user, self)
        remove_perm(Source.PermTypes.VIEW.code, user, self)


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

    def num_of_keys(self):
        """
        Return the number of location keys that this Source has.
        """
        return len(self.get_key_list())

    def location_value_field_names(self):
        """
        Return the names of the location value fields that this source
        uses, as a list:
        ['value1', 'value2', 'value3']
        """
        all_fields = ['value1', 'value2', 'value3', 'value4', 'value5']
        return all_fields[:self.num_of_keys()]

    def image_annotation_area_display(self):
        """
        Display the annotation-area parameters in templates.
        Usage: {{ mysource.annotation_area_display }}
        """
        return AnnotationAreaUtils.db_format_to_display(self.image_annotation_area)

    def point_gen_method_display(self):
        """
        Display the point generation method in templates.
        Usage: {{ mysource.point_gen_method_display }}
        """
        return PointGen.db_to_readable_format(self.default_point_generation_method)

    def annotation_area_display(self):
        """
        Display the annotation area parameters in templates.
        Usage: {{ mysource.annotation_area_display }}
        """
        return AnnotationAreaUtils.db_format_to_display(self.image_annotation_area)

    def get_latest_robot(self):
        """
        return the latest robot associated with this source.
        if no robots, return None
        """
        validRobots = self.get_valid_robots()
        
        if len(validRobots) > 0:
        	return validRobots[-1]
        else:
        	return None

    def get_valid_robots(self):
        """
        returns a list of all robots that have valid metadata
        """
        allRobots = Robot.objects.filter(source = self).order_by('version')
        validRobots = []
        for thisRobot in allRobots:
            # check that the meta-data exists and that the actual model file exists.
            if os.path.exists(thisRobot.path_to_model + '.meta.json'):
                try: # check that we can actually read the meta data
                    f = open(thisRobot.path_to_model + '.meta.json')
                    meta = json.loads(f.read())
                    f.close()
                    validRobots.append(thisRobot)
                except:
                    continue
        return validRobots

    def need_new_robot(self):
        """
        Check whether there are sufficient number of newly annotated images to train a new robot version. Needs to be settings.NEW_MODEL_THRESHOLD more than used in the previous model and > settings.MIN_NBR_ANNOTATED_IMAGES
        """
        
        return Image.objects.filter(source=self, status__annotatedByHuman = True).count() > settings.NEW_MODEL_THRESHOLD * Image.objects.filter(source=self, status__usedInCurrentModel = True).count() and Image.objects.filter(source=self, status__annotatedByHuman = True).count() >= settings.MIN_NBR_ANNOTATED_IMAGES and self.enable_robot_classifier

    def has_robot(self):
        """
        Returns true if source has a robot.
        """
        if Robot.objects.filter(source=self).count() == 0:
            return False
        else:
            return True

    def remove_unused_key_values(self):
        """
        Finds all of the key values used by this source and removes unused ones.
        """
        images = self.get_all_images()

        for key, valueClass in [
                (self.key1, Value1),
                (self.key2, Value2),
                (self.key3, Value3),
                (self.key4, Value4),
                (self.key5, Value5)
                ]:
            if key:
                values = valueClass.objects.filter(source=self)
                for value in values:
                    used = False
                    for image in images:
                        if valueClass == Value1:
                            if image.metadata.value1 == value:
                                used = True
                                break
                        if valueClass == Value2:
                            if image.metadata.value2 == value:
                                used = True
                                break
                        if valueClass == Value3:
                            if image.metadata.value3 == value:
                                used = True
                                break
                        if valueClass == Value4:
                            if image.metadata.value4 == value:
                                used = True
                                break
                        if valueClass == Value5:
                            if image.metadata.value5 == value:
                                used = True
                                break
                    if not used:
                        value.delete()

    def all_image_names_are_unique(self):
        """
        Return true if all images in the source have unique names. NOTE: this will be enforced during import moving forward, but it wasn't originally.
        """
        images = Image.objects.filter(source=self)
        nimages = images.count()
        nunique = len(set([i.metadata.name for i in images]))
        return nunique == images.count()

    def get_nonunique_image_names(self):
        """
        returns a list of image names which occur for multiple images in the source. NOTE: there is probably a fancy SQL way to do this, but I found it cleaner with a python solution. It's not time critical.
        """
        imnames = [i.metadata.name for i in Image.objects.filter(source=self)] 
        return list(set([name for name in imnames if imnames.count(name) > 1]))

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

        # Default ordering criteria.
        ordering = ['name']

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
    photo_date = models.DateField(
        "Date",
        help_text='Format: YYYY-MM-DD',
        null=True, blank=True,
    )

    latitude = models.CharField("Latitude", max_length=20, blank=True)
    longitude = models.CharField("Longitude", max_length=20, blank=True)
    depth = models.CharField("Depth", max_length=45, blank=True)

    height_in_cm = models.IntegerField(
        "Height (cm)",
        help_text="What is the actual span between the top and bottom of this image?\n"
                  "(This information is used by the automatic annotator.)",
        validators=[MinValueValidator(ImageModelConstants.MIN_IMAGE_CM_HEIGHT),
                    MaxValueValidator(ImageModelConstants.MAX_IMAGE_CM_HEIGHT)],
        null=True, blank=True
    )

    annotation_area = models.CharField(
        "Annotation area",
        help_text="This defines a rectangle of the image where annotation points are allowed to be generated. "
                  "If you change this, then new points will be generated for this image, and the old points will be deleted.",
        max_length=50,
        null=True, blank=True
    )
    
    camera = models.CharField("Camera", max_length=200, blank=True)
    photographer = models.CharField("Photographer", max_length=45, blank=True)
    water_quality = models.CharField("Water quality", max_length=45, blank=True)

    strobes = models.CharField("Strobes", max_length=200, blank=True)
    framing = models.CharField("Framing gear used", max_length=200, blank=True)
    balance = models.CharField("White balance card", max_length=200, blank=True)
    
    comments = models.TextField(max_length=1000, blank=True)
    
    value1 = models.ForeignKey(Value1, null=True, blank=True)
    value2 = models.ForeignKey(Value2, null=True, blank=True)
    value3 = models.ForeignKey(Value3, null=True, blank=True)
    value4 = models.ForeignKey(Value4, null=True, blank=True)
    value5 = models.ForeignKey(Value5, null=True, blank=True)

    def __unicode__(self):
        return "Metadata of " + self.name


class ImageStatus(models.Model):
    # Image is preprocessed with the desired parameters (cm height, etc.)
    preprocessed = models.BooleanField(default=False)
    # Image has annotation points
    hasRandomPoints = models.BooleanField(default=False)
    # Features have been extracted for the current annotation points
    featuresExtracted = models.BooleanField(default=False)
    # All of the current points have been annotated by robot at some point
    # (it's OK if the annotations were overwritten by human)
    annotatedByRobot = models.BooleanField(default=False)
    # Image is 100% annotated by human
    annotatedByHuman = models.BooleanField(default=False)
    # Feature file includes the completed, human-annotated labels
    featureFileHasHumanLabels = models.BooleanField(default=False)
    # This source's current robot model uses said feature file
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

    def get_image_element_title(self):
        """
        Use this as the "title" element of the image on an HTML page
        (hover the mouse over the image to see this).
        """
        # Just use the image name (usually filename).
        return self.metadata.name

    def get_annotation_status_code(self):
        """
        Returns a code for the annotation status of this image.
        """
        if self.source.enable_robot_classifier:
            if self.status.annotatedByHuman:
                return "confirmed"
            elif self.status.annotatedByRobot:
                return "unconfirmed"
            else:
                return "needs_annotation"
        else:
            if self.status.annotatedByHuman:
                return "annotated"
            else:
                return "needs_annotation"

    def get_annotation_status_str(self):
        """
        Returns a string describing the annotation status of this image.
        """
        code = self.get_annotation_status_code()
        if code == "confirmed":
            return "Confirmed"
        elif code == "unconfirmed":
            return "Unconfirmed"
        elif code == "needs_annotation":
            return "Needs annotation"
        elif code == "annotated":
            return "Annotated"

    def get_metadata_values_for_export(self):
        exportfields = ['annotation_area', 'balance', 'camera', 'comments', \
        'depth', 'framing', 'height_in_cm', 'latitude', 'longitude', \
        'name', 'photographer', 'strobes', 'water_quality'];
        out = [];
        for e in exportfields:
            out.append(getattr(self.metadata,e))
        return out

    def get_metadata_fields_for_export(self):

        exportfields = ['Annotation area', 'White Balance', 'Camera', 'Comments', \
        'Depth', 'Framing gear', 'Image Height (cm)', 'Latitude', 'Longitude', \
        'Original File Name', 'Photographer', 'Strobes', 'Water quality'];
        return exportfields

    def get_location_value_str_list(self):
        """
        Returns the image's location values as a list of strings:
        ['Shore3', 'Reef 5', 'Loc10']
        Add one list item per value field used by the source. If this
        image isn't using one of the value fields, the corresponding
        list item will be an empty string:
        ['Shore2', '', 'Loc7']
        """
        field_names = self.source.location_value_field_names()

        value_name_list = []
        for field_name in field_names:
            value_object = getattr(self.metadata, field_name)
            if value_object:
                value_name_list.append(value_object.name)
            else:
                value_name_list.append('')
        return value_name_list

    def get_location_value_str_list_robust(self):
        """
        Returns the image's location values as a list of strings:
        ['Shore3', 'Reef 5', 'Loc10']
        This file will return the value 'not_specified' for each key 
        where there is no location value specified.
        """

        valueList = []
        metadata = self.metadata

        nkeys = len(self.source.get_key_list())


        L = ['value1', 'value2', 'value3', 'value4', 'value5']
        
        for i in range(nkeys):
            valueObj = getattr(metadata, L[i])
            if valueObj:
                valueList.append(valueObj.name)
            else:
                valueList.append("not_specified")

        return valueList

    def get_year_and_location_values(self):
        """
        Get the year and location values for display as a 2 x n table.
        """
        metadata = self.metadata
        source = self.source
        dataTupleList = []

        if metadata.photo_date:
            dataTupleList.append( ("Year", str(metadata.photo_date.year)) )
        else:
            dataTupleList.append( ("Year", "") )

        for keyName, valueObj in [
            (source.key1, metadata.value1),
            (source.key2, metadata.value2),
            (source.key3, metadata.value3),
            (source.key4, metadata.value4),
            (source.key5, metadata.value5)
        ]:
            if keyName:
                if valueObj:
                    dataTupleList.append( (keyName, valueObj.name) )
                else:
                    dataTupleList.append( (keyName, "") )

        dataTwoLists = dict(
            keys=[t[0] for t in dataTupleList],
            values=[t[1] for t in dataTupleList],
        )
        return dataTwoLists

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
        if self.metadata.height_in_cm:
            imheight = self.metadata.height_in_cm

        return imheight

    def after_height_cm_change(self):
        status = self.status
        status.preprocessed = False
        status.featuresExtracted = False
        status.annotatedByRobot = False
        status.featureFileHasHumanLabels = False
        status.usedInCurrentModel = False
        status.save()

    def after_deleting_annotations(self):
        status = self.status
        status.featureFileHasHumanLabels = False
        status.annotatedByHuman = False
        status.annotatedByRobot = False
        status.usedInCurrentModel = False
        status.save()

    def annotation_area_display(self):
        """
        Display the annotation area parameters in templates.
        Usage: {{ myimage.annotation_area_display }}
        """
        return AnnotationAreaUtils.db_format_to_display(self.metadata.annotation_area)

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
