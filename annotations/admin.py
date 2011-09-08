from annotations.models import Label, LabelSet, LabelGroup
from django.contrib import admin

class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'group', 'create_date')

class LabelSetAdmin(admin.ModelAdmin):
    pass

class LabelGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')

admin.site.register(Label, LabelAdmin)
admin.site.register(LabelSet, LabelSetAdmin)
admin.site.register(LabelGroup, LabelGroupAdmin)
