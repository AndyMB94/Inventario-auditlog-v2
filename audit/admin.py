from django.contrib import admin
from audit.models import AuditModelConfig

@admin.register(AuditModelConfig)
class AuditModelConfigAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('content_type__app_label', 'content_type__model')