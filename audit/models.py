from django.db import models
from django.contrib.contenttypes.models import ContentType

class AuditModelConfig(models.Model):
    content_type = models.OneToOneField(
        ContentType,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.content_type.app_label}.{self.content_type.model} - {self.is_active}"