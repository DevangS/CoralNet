from images.models import Source
from django.contrib import admin

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'visibility', 'create_date')

admin.site.register(Source, SourceAdmin)
