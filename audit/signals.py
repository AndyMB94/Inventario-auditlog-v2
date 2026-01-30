from auditlog.signals import post_log
from audit.models import AuditModelConfig

def auditlog_post_log_handler(sender, **kwargs):
    log_entry = kwargs.get("log_entry")

    if not log_entry:
        return

    # ¿Existe config activa?
    is_active = AuditModelConfig.objects.filter(
        content_type=log_entry.content_type,
        is_active=True
    ).exists()

    # Si NO está activo → borrar log
    if not is_active:
        log_entry.delete()

post_log.connect(auditlog_post_log_handler)
