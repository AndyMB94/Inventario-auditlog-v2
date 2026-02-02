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
