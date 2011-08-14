from images.models import Source, Image, Metadata
from django.contrib import admin
from guardian.admin import GuardedModelAdmin

class SourceAdmin(GuardedModelAdmin):
    list_display = ('name', 'visibility', 'create_date')

class ImageAdmin(admin.ModelAdmin):
    list_display = ('original_file', 'source', 'metadata')

class MetadataAdmin(admin.ModelAdmin):
    list_display = ('name', 'value1', 'value2', 'value3', 'value4', 'value5')

admin.site.register(Source, SourceAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Metadata, MetadataAdmin)
