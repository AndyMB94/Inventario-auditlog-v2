from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        import audit.signals

        # Re-registrar todos los modelos con serialize_data=True
        from auditlog.registry import auditlog

        # Obtener todos los modelos actualmente registrados
        registered_models = list(auditlog.get_models())

        for model in registered_models:
            try:
                auditlog.unregister(model)
                auditlog.register(model, serialize_data=True)
            except Exception:
                pass