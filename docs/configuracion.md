# Configuracion del Sistema de Auditoria

Guia paso a paso para configurar el sistema de auditoria centralizada con control dinamico por modelo en un proyecto Django.

---

## Requisitos

- Python 3.10+
- Django 5.x
- Django REST Framework (si usas API)
- SimpleJWT (si usas autenticacion JWT)

---

## Paso 1: Instalar dependencias

```bash
pip install django-auditlog
```

Agregar a `requirements.txt`:
```
django-auditlog==3.4.1
```

---

## Paso 2: Configurar settings.py

### 2.1 INSTALLED_APPS

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'auditlog',                     # django-auditlog

    # Local apps
    'inventory',                    # Tu app de negocio
    'audit.apps.AuditConfig',       # App de control de auditoria (crear en paso 3)
]
```

### 2.2 MIDDLEWARE

El orden es importante:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'store.middleware.JWTAuthenticationMiddleware',  # ANTES de auditlog (si usas JWT)
    'auditlog.middleware.AuditlogMiddleware',        # Captura usuario e IP
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### 2.3 Configuracion de auditlog

```python
AUDITLOG_INCLUDE_ALL_MODELS = True  # Registra todos los modelos automaticamente
```

---

## Paso 3: Crear la app audit

```bash
python manage.py startapp audit
```

### 3.1 audit/models.py

```python
from django.db import models
from django.contrib.contenttypes.models import ContentType


class AuditModelConfig(models.Model):
    content_type = models.OneToOneField(
        ContentType,
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.content_type.app_label}.{self.content_type.model} - {'Activo' if self.is_active else 'Inactivo'}"

    class Meta:
        verbose_name = 'Configuracion de Auditoria'
        verbose_name_plural = 'Configuraciones de Auditoria'
```

### 3.2 audit/signals.py

```python
from auditlog.signals import post_log
from audit.models import AuditModelConfig


def auditlog_post_log_handler(sender, **kwargs):
    log_entry = kwargs.get("log_entry")

    if not log_entry:
        return

    # Verificar si el modelo tiene auditoria activa
    is_active = AuditModelConfig.objects.filter(
        content_type=log_entry.content_type,
        is_active=True
    ).exists()

    # Si no esta activo, eliminar el log
    if not is_active:
        log_entry.delete()


post_log.connect(auditlog_post_log_handler)
```

### 3.3 audit/apps.py

```python
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
```

**Que hace:**
- `post_migrate`: Crea `AuditModelConfig` automaticamente despues de cada `migrate`
- Re-registro: Habilita `serialize_data=True` para todos los modelos

### 3.4 audit/admin.py

```python
from django.contrib import admin
from audit.models import AuditModelConfig


@admin.register(AuditModelConfig)
class AuditModelConfigAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('content_type__app_label', 'content_type__model')
    list_editable = ('is_active',)
```

### 3.5 Comando de inicializacion

Crear estructura de carpetas:
```
audit/
└── management/
    └── commands/
        └── init_audit_models.py
```

Contenido de `audit/management/commands/init_audit_models.py`:

```python
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from audit.models import AuditModelConfig


class Command(BaseCommand):
    help = "Inicializa configuraciones de auditoria para todos los modelos"

    def handle(self, *args, **kwargs):
        created_count = 0
        for ct in ContentType.objects.all():
            _, created = AuditModelConfig.objects.get_or_create(
                content_type=ct,
                defaults={"is_active": False}
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"AuditModelConfig inicializado. {created_count} nuevas configuraciones creadas."
            )
        )
```

---

## Paso 4: Middleware JWT (si usas JWT)

Si usas SimpleJWT, necesitas un middleware para que auditlog capture el usuario correctamente.

Crear `store/middleware.py` (o en tu carpeta de proyecto):

```python
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            auth = JWTAuthentication()
            auth_result = auth.authenticate(request)
            if auth_result:
                request.user, _ = auth_result
        except Exception:
            pass
        return self.get_response(request)
```

**Por que es necesario:**
- Django REST Framework autentica JWT en la capa de vistas
- AuditlogMiddleware captura el usuario en la capa de middleware
- Sin este middleware, auditlog veria `request.user` como anonimo

---

## Paso 5: Aplicar migraciones

```bash
python manage.py makemigrations audit
python manage.py migrate
```

---

## Paso 6: Activar auditoria por modelo

La configuracion `AuditModelConfig` se crea **automaticamente** al ejecutar `migrate` gracias al signal `post_migrate`.

1. Acceder a `/admin/audit/auditmodelconfig/`
2. Marcar `is_active=True` en los modelos que deseas auditar
3. Guardar

Los cambios aplican inmediatamente sin reiniciar el servidor.

---

## Resumen de archivos

```
proyecto/
├── store/
│   ├── settings.py          # Configuracion de apps y middleware
│   └── middleware.py        # JWTAuthenticationMiddleware
├── audit/
│   ├── __init__.py
│   ├── admin.py             # Interfaz de administracion
│   ├── apps.py              # Re-registro con serialize_data
│   ├── models.py            # AuditModelConfig
│   ├── signals.py           # Filtrado de logs
│   └── management/
│       └── commands/
│           └── init_audit_models.py
└── requirements.txt         # django-auditlog
```

---

## Verificar funcionamiento

1. Activar auditoria para un modelo (ej: `inventory.product`)
2. Crear/editar/eliminar un registro de ese modelo
3. Verificar en `/admin/auditlog/logentry/` que se creo el log
4. Verificar que `serialized_data` tiene contenido

---

## Agregar nuevos modelos

Cuando crees nuevos modelos en tu proyecto:

```bash
python manage.py makemigrations
python manage.py migrate
```

La configuracion `AuditModelConfig` se crea **automaticamente** gracias al signal `post_migrate`. No necesitas ejecutar comandos adicionales.

Luego activa la auditoria en el admin si lo deseas.

---

## Troubleshooting

### El usuario aparece como anonimo en los logs
- Verificar que `JWTAuthenticationMiddleware` esta ANTES de `AuditlogMiddleware`
- Verificar que el token JWT es valido

### serialized_data esta vacio
- Verificar que `audit/apps.py` tiene el codigo de re-registro
- Verificar que la app es `audit.apps.AuditConfig` en INSTALLED_APPS
- Reiniciar el servidor

### Los logs no se crean
- Verificar que `AUDITLOG_INCLUDE_ALL_MODELS = True`
- Verificar que el modelo tiene `is_active=True` en AuditModelConfig
- Ejecutar `python manage.py migrate` para crear configuraciones faltantes

### Los logs se crean pero no se filtran
- Verificar que `audit/signals.py` tiene el handler conectado
- Verificar que `audit/apps.py` importa los signals en `ready()`

---

## Configuracion Avanzada: Activity Tracking

Ademas de auditar CREATE/UPDATE/DELETE automaticamente con django-auditlog, puedes auditar:
- **Lecturas (LIST/RETRIEVE)**: Cuando un usuario consulta datos
- **Autenticacion (LOGIN/LOGOUT)**: Cuando un usuario ingresa o sale del sistema
- **Exportaciones**: Cuando un usuario descarga datos en Excel/PDF

### Paso 1: Crear audit/tracking.py

```python
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
    """Registra una actividad personalizada en LogEntry"""
    if user and not user.is_authenticated:
        user = None

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
```

### Paso 2: Crear audit/mixins.py

```python
from audit.tracking import log_read_list, log_read_detail


class AuditReadMixin:
    """Mixin para ViewSets que registra operaciones de lectura (list, retrieve)"""

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            extra_data = {
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'count': len(response.data.get('results', response.data)) if isinstance(response.data, dict) else len(response.data)
            }

            log_read_list(
                user=request.user if request.user.is_authenticated else None,
                model_class=self.queryset.model,
                extra_data=extra_data
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            instance = self.get_object()
            extra_data = {
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }

            log_read_detail(
                user=request.user if request.user.is_authenticated else None,
                instance=instance,
                extra_data=extra_data
            )

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### Paso 3: Actualizar audit/signals.py

Agregar tracking de login/logout:

```python
from auditlog.signals import post_log
from audit.models import AuditModelConfig
from django.contrib.auth.signals import user_logged_in, user_logged_out
from audit.tracking import log_login, log_logout


def auditlog_post_log_handler(sender, **kwargs):
    log_entry = kwargs.get("log_entry")
    if not log_entry:
        return

    is_active = AuditModelConfig.objects.filter(
        content_type=log_entry.content_type,
        is_active=True
    ).exists()

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
```

### Paso 4: Aplicar AuditReadMixin a ViewSets

En tus ViewSets (ej: `inventory/views.py`):

```python
from audit.mixins import AuditReadMixin

class ProductViewSet(AuditReadMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # ... resto del codigo
```

### Paso 5: Tracking de Exportaciones

Para endpoints de exportacion (Excel/PDF):

```python
from audit.tracking import log_export
from rest_framework.decorators import action
from openpyxl import Workbook

class ProductViewSet(AuditReadMixin, viewsets.ModelViewSet):
    # ... codigo existente

    @action(detail=False, methods=['get'], url_path='export')
    def export_to_excel(self, request):
        products = self.get_queryset()

        # Generar Excel...
        wb = Workbook()
        # ... logica de exportacion

        # Registrar en auditlog
        log_export(
            user=request.user,
            model_class=Product,
            export_format='excel',
            extra_data={'count': products.count()}
        )

        return response
```

### Tipos de Accion

| Codigo | Accion | Registro |
|--------|--------|----------|
| 0 | CREATE | Automatico (django-auditlog) |
| 1 | UPDATE | Automatico (django-auditlog) |
| 2 | DELETE | Automatico (django-auditlog) |
| 3 | ACCESS | Nativo (auditlog) + Manual (AuditReadMixin) |
| 4 | LOGIN | Automatico (signal) |
| 5 | LOGOUT | Automatico (signal) |
| 6 | EXPORT | Manual (en vista de export) |

### Instalar dependencias adicionales

```bash
pip install openpyxl  # Para exportacion a Excel
```
