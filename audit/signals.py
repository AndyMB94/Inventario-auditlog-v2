from auditlog.signals import post_log
from audit.models import AuditModelConfig
from django.contrib.auth.signals import user_logged_in, user_logged_out
from audit.tracking import log_login, log_logout


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


def user_logged_in_handler(sender, request, user, **kwargs):
    """Registra cuando un usuario hace login"""
    extra_data = {
        'ip': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }
    log_login(user=user, extra_data=extra_data)


def user_logged_out_handler(sender, request, user, **kwargs):
    """Registra cuando un usuario hace logout"""
    extra_data = {
        'ip': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }
    log_logout(user=user, extra_data=extra_data)


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Conectar signals
post_log.connect(auditlog_post_log_handler)
user_logged_in.connect(user_logged_in_handler)
user_logged_out.connect(user_logged_out_handler)
