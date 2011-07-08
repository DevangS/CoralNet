from django.db import models

class Source(models.Model):

    # Example: 'Moorea'
    name = models.CharField(max_length=200)

    # This determines the visibility setting of the image source.
    # 'public' = images are visible to the public by default
    # 'private' = images are visible only to the source participators by default
    # 'invisible' = private images + the project's existence is not known to the public
    visibility = models.CharField(max_length=20)

    create_date = models.DateTimeField()

    # To-string method
    def __unicode__(self):
        return "Name: " + self.name \
               + "\nVisibility: " + self.visibility \
               + "\nDate created: " + str(self.create_date)
