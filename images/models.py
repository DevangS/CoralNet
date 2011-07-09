from django.db import models

class Source(models.Model):

    # Example: 'Moorea'
    name = models.CharField(max_length=200)

    # This determines the visibility setting of the image source.
    # 'public' = images are visible to the public by default
    # 'private' = images are visible only to the source participators by default
    # 'invisible' = private images + the project's existence is not known to the public
    visibility = models.CharField(max_length=1)

    # Allow us to go from 'b' to 'public' or vice versa
    visibilityCodeToStr = {'b':'public', 'v':'private', 'i':'invisible'}
    visibilityStrToCode = dict( [(b,a) for (a,b) in visibilityCodeToStr.items()] )

    create_date = models.DateTimeField('date created')

    # Each of these fields is allowed to be blank (an empty string).
    # We're assuming that we'll only have key 2 if we have
    # key 1, we'll only have key 3 if we have key 2, etc.
    key1 = models.CharField('location key 1', max_length=50, blank=True)
    key2 = models.CharField('location key 2', max_length=50, blank=True)
    key3 = models.CharField('location key 3', max_length=50, blank=True)
    key4 = models.CharField('location key 4', max_length=50, blank=True)
    key5 = models.CharField('location key 5', max_length=50, blank=True)

    longitude = models.CharField(max_length=20, blank=True)
    latitude = models.CharField(max_length=20, blank=True)

    def visibilityStr(self):
        return self.visibilityCodeToStr[self.visibility]

    # To-string method
    def __unicode__(self):
        displayStr = "\nName: " + self.name \
               + "\nVisibility: " + self.visibilityStr() \
               + "\nDate created: " + str(self.create_date)
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
