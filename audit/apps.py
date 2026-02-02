from django.apps import AppConfig
from django.db.models.signals import post_migrate


def init_audit_models_after_migrate(sender, **kwargs):
    """Se ejecuta automaticamente despues de cada migrate"""
    from django.contrib.contenttypes.models import ContentType
    from audit.models import AuditModelConfig

    for ct in ContentType.objects.all():
        AuditModelConfig.objects.get_or_create(
            content_type=ct,
            defaults={"is_active": False}
        )


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        import audit.signals

        # Ejecutar init_audit_models automaticamente despues de cada migrate
        post_migrate.connect(init_audit_models_after_migrate, sender=self)

        # Re-registrar todos los modelos con serialize_data=True
        from auditlog.registry import auditlog

        registered_models = list(auditlog.get_models())

        for model in registered_models:
            try:
                auditlog.unregister(model)
                auditlog.register(model, serialize_data=True)
            except Exception:
                pass
