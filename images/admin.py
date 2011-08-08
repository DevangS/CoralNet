from images.models import Source
from django.contrib import admin
from guardian.admin import GuardedModelAdmin

class SourceAdmin(GuardedModelAdmin):
    list_display = ('name', 'visibility', 'create_date')

admin.site.register(Source, SourceAdmin)
