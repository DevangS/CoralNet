from annotations.models import Label, LabelSet, LabelGroup, Annotation
from django.contrib import admin
import reversion

class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'group', 'create_date')

class LabelSetAdmin(admin.ModelAdmin):
    pass

class LabelGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

# Inherit from reversion.VersionAdmin to enable versioning for a particular model.
class AnnotationAdmin(reversion.VersionAdmin):
    list_display = ('source', 'image', 'point')

admin.site.register(Label, LabelAdmin)
admin.site.register(LabelSet, LabelSetAdmin)
admin.site.register(LabelGroup, LabelGroupAdmin)
admin.site.register(Annotation, AnnotationAdmin)
