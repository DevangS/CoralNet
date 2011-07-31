from django.db import models
from django.contrib.auth.models import User

class Feedback(models.Model):

    FEEDBACK_TYPE_CHOICES = {
        ('b', "Bug Report"),
        ('r', "Suggestion / Request"),
        ('f', "Feedback / Other"),
    }
    type = models.CharField(max_length=1, choices=FEEDBACK_TYPE_CHOICES)

    comment = models.TextField('Description / Comment')
    user = models.ForeignKey(User)
    date = models.DateTimeField('Date', auto_now_add=True, editable=False)

    # Will be auto-filled in when the feedback form is reached from a 500 error.
    # Otherwise, this field isn't used.
    error_id = models.CharField(max_length=100, blank=True, editable=False)
    
    # Browser info (get automatically)?
    # OS info (get automatically)?
    # URL that they came from (get automatically)? (Would this even be useful?)