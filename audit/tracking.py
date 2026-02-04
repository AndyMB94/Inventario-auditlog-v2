from django.contrib.contenttypes.models import ContentType
from auditlog.models import LogEntry


# Constantes para tipos de accion
class ActionType:
    CREATE = 0
    UPDATE = 1
    DELETE = 2
    ACCESS = 3   # usado por auditlog nativo; se usa tambien para LIST y RETRIEVE
    LOGIN = 4
    LOGOUT = 5
    EXPORT = 6


def log_activity(user, action, content_type=None, object_id=None, object_repr=None, extra_data=None, remote_addr=None):
    """
    Registra una actividad personalizada en LogEntry.

    Args:
        user: Usuario que realiza la accion
        action: Tipo de accion (usar ActionType)
        content_type: ContentType del modelo (opcional)
        object_id: ID del objeto (opcional)
        object_repr: Representacion del objeto (opcional)
        extra_data: Datos adicionales en formato dict (opcional)
        remote_addr: IP del cliente (opcional)

    Returns:
        LogEntry creado
    """
    if user and not user.is_authenticated:
        user = None

    # Extraer IP de extra_data si existe
    ip = remote_addr or (extra_data.get('ip') if extra_data else None)

    log_entry = LogEntry.objects.create(
        actor=user,
        action=action,
        content_type=content_type,
        object_id=str(object_id) if object_id else None,
        object_repr=object_repr or '',
        additional_data=extra_data or {},
        remote_addr=ip,
        actor_email=user.email if user else None
    )

    return log_entry


def log_read_list(user, model_class, extra_data=None):
    """Helper para registrar operacion LIST"""
    content_type = ContentType.objects.get_for_model(model_class)
    return log_activity(
        user=user,
        action=ActionType.ACCESS,
        content_type=content_type,
        object_repr=f"List {model_class._meta.verbose_name_plural}",
        extra_data=extra_data
    )


def log_read_detail(user, instance, extra_data=None):
    """Helper para registrar operacion RETRIEVE"""
    content_type = ContentType.objects.get_for_model(instance)
    return log_activity(
        user=user,
        action=ActionType.ACCESS,
        content_type=content_type,
        object_id=instance.pk,
        object_repr=str(instance),
        extra_data=extra_data
    )


def log_export(user, model_class, export_format, extra_data=None):
    """Helper para registrar exportaciones"""
    content_type = ContentType.objects.get_for_model(model_class)
    extra = extra_data or {}
    extra['export_format'] = export_format

    return log_activity(
        user=user,
        action=ActionType.EXPORT,
        content_type=content_type,
        object_repr=f"Export {model_class._meta.verbose_name_plural} to {export_format}",
        extra_data=extra
    )


def log_login(user, extra_data=None):
    """Helper para registrar login"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    content_type = ContentType.objects.get_for_model(User)

    return log_activity(
        user=user,
        action=ActionType.LOGIN,
        content_type=content_type,
        object_id=user.pk,
        object_repr=f"Login: {user.username}",
        extra_data=extra_data
    )


def log_logout(user, extra_data=None):
    """Helper para registrar logout"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    content_type = ContentType.objects.get_for_model(User)

    return log_activity(
        user=user,
        action=ActionType.LOGOUT,
        content_type=content_type,
        object_id=user.pk,
        object_repr=f"Logout: {user.username}",
        extra_data=extra_data
    )
