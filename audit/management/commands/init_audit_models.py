from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from audit.models import AuditModelConfig

class Command(BaseCommand):
    help = "Inicializa configuraciones de auditoría por modelo"

    def handle(self, *args, **kwargs):
        for ct in ContentType.objects.all():
            AuditModelConfig.objects.get_or_create(
                content_type=ct,
                defaults={"is_active": False}
            )
        self.stdout.write(self.style.SUCCESS("AuditModelConfig inicializado"))
