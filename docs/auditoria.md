# Sistema de Auditoria

El sistema registra automaticamente todas las operaciones CRUD en la tabla `auditlog_logentry`, con **control dinamico por modelo** desde la base de datos.

## Caracteristica principal

A diferencia de la configuracion tradicional de django-auditlog (que requiere modificar codigo), este proyecto permite:

- **Activar/desactivar auditoria por modelo desde el admin**
- **Cambios en tiempo real** sin reiniciar el servidor
- **Control centralizado** en una sola tabla

---

## Arquitectura

```
                                    ┌─────────────────────┐
                                    │   AuditModelConfig  │
                                    │   (audit/models.py) │
                                    │                     │
                                    │ content_type: FK    │
                                    │ is_active: Boolean  │
                                    └──────────┬──────────┘
                                               │
                                               │ consulta
                                               ▼
┌──────────┐    ┌──────────────┐    ┌─────────────────────┐    ┌────────────┐
│  Request │───▶│ Auditlog crea│───▶│ Signal post_log     │───▶│ LogEntry   │
│  (CRUD)  │    │  LogEntry    │    │ (audit/signals.py)  │    │ guardado   │
└──────────┘    └──────────────┘    │                     │    └────────────┘
                                    │ if is_active=False: │
                                    │   log_entry.delete()│
                                    └─────────────────────┘
```

---

## Componentes

### 1. Modelo de Configuracion

**Ubicacion:** `audit/models.py`

```python
class AuditModelConfig(models.Model):
    content_type = models.OneToOneField(ContentType, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
```

| Campo | Descripcion |
|-------|-------------|
| `content_type` | Referencia al modelo (ej: `inventory.product`) |
| `is_active` | `True` = auditar, `False` = no auditar |

### 2. Signal Handler

**Ubicacion:** `audit/signals.py`

```python
from auditlog.signals import post_log
from audit.models import AuditModelConfig

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

post_log.connect(auditlog_post_log_handler)
```

**Flujo:**
1. Auditlog crea un `LogEntry` para cada cambio
2. Se dispara el signal `post_log`
3. El handler verifica si el modelo tiene `is_active=True`
4. Si es `False`, elimina el log inmediatamente

### 3. Auto-registro y configuracion automatica

**Ubicacion:** `audit/apps.py`

```python
from django.apps import AppConfig
from django.db.models.signals import post_migrate


def init_audit_models_after_migrate(_sender, **_kwargs):
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
- No necesitas ejecutar comandos manuales

### 4. Comando de Inicializacion (opcional)

**Ubicacion:** `audit/management/commands/init_audit_models.py`

```bash
python manage.py init_audit_models
```

Este comando es **opcional** ya que la inicializacion ahora es automatica via `post_migrate`. Solo usalo si necesitas forzar la creacion de configuraciones manualmente.

---

## Configuracion en settings.py

```python
INSTALLED_APPS = [
    # ...
    'auditlog',
    'audit.apps.AuditConfig',
]

MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'store.middleware.JWTAuthenticationMiddleware',  # Autentica JWT
    'auditlog.middleware.AuditlogMiddleware',        # Captura contexto
]

AUDITLOG_INCLUDE_ALL_MODELS = True  # Registra TODOS los modelos automaticamente
```

---

## Campos registrados en LogEntry

| Campo | Descripcion |
|-------|-------------|
| `actor_id` | ID del usuario que realizo la accion |
| `actor_email` | Email del usuario |
| `action` | Tipo de accion (ver tabla abajo) |
| `timestamp` | Fecha y hora de la accion |
| `remote_addr` | IP del cliente |
| `changes` | Cambios realizados en formato JSON (solo CREATE/UPDATE/DELETE) |
| `serialized_data` | Copia completa del objeto (habilitado via apps.py) |
| `additional_data` | Datos extra (IP, user-agent, count, etc.) |

### Tipos de Accion

| Codigo | Accion | Origen | Descripcion |
|--------|--------|--------|-------------|
| 0 | CREATE | django-auditlog | Creacion automatica |
| 1 | UPDATE | django-auditlog | Actualizacion automatica |
| 2 | DELETE | django-auditlog | Eliminacion automatica |
| 3 | ACCESS | Nativo (auditlog) + AuditReadMixin | Listado y consulta de registros |
| 4 | LOGIN | Custom (signal) | Login de usuario |
| 5 | LOGOUT | Custom (signal) | Logout de usuario |
| 6 | EXPORT | Custom (manual) | Exportacion (Excel/PDF) |

## Ejemplos de registros

### UPDATE (action=1)
```json
{
    "id": 1,
    "actor_id": 1,
    "actor_email": "admin@admin.com",
    "action": 1,
    "object_repr": "Laptop HP",
    "timestamp": "2026-01-29T16:55:12Z",
    "remote_addr": "127.0.0.1",
    "changes": {
        "price": ["1500.00", "1200.00"],
        "stock": ["10", "15"]
    },
    "serialized_data": {
        "id": 1,
        "name": "Laptop HP",
        "category": 1,
        "price": "1200.00",
        "stock": 15
    },
    "additional_data": {}
}
```

### ACCESS - Listado (action=3)
```json
{
    "id": 2,
    "actor_id": 1,
    "actor_email": "admin@admin.com",
    "action": 3,
    "object_repr": "List products",
    "object_id": null,
    "timestamp": "2026-02-03T17:00:00Z",
    "remote_addr": "127.0.0.1",
    "changes": null,
    "serialized_data": null,
    "additional_data": {
        "ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0...",
        "count": 104
    }
}
```

### ACCESS - Detalle (action=3)
```json
{
    "id": 3,
    "actor_id": 1,
    "actor_email": "admin@admin.com",
    "action": 3,
    "object_repr": "Laptop HP",
    "object_id": "1",
    "timestamp": "2026-02-03T17:01:00Z",
    "remote_addr": "127.0.0.1",
    "changes": null,
    "serialized_data": null,
    "additional_data": {
        "ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0..."
    }
}
```

### LOGIN (action=4)
```json
{
    "id": 4,
    "actor_id": 1,
    "actor_email": "admin@admin.com",
    "action": 4,
    "object_repr": "Login: admin",
    "timestamp": "2026-02-03T16:55:13Z",
    "remote_addr": "127.0.0.1",
    "changes": null,
    "serialized_data": null,
    "additional_data": {
        "ip": "127.0.0.1",
        "user_agent": "Mozilla/5.0..."
    }
}
```

### EXPORT (action=6)
```json
{
    "id": 5,
    "actor_id": 1,
    "actor_email": "admin@admin.com",
    "action": 6,
    "object_repr": "Export products to excel",
    "timestamp": "2026-02-03T17:10:00Z",
    "remote_addr": "127.0.0.1",
    "changes": null,
    "serialized_data": null,
    "additional_data": {
        "count": 104,
        "ip": "127.0.0.1",
        "export_format": "excel"
    }
}
```

---

## Middlewares

Para que la auditoria funcione correctamente con JWT, se implementaron dos middlewares:

```python
MIDDLEWARE = [
    # ... otros middlewares ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'store.middleware.JWTAuthenticationMiddleware',  # 1. Autentica JWT
    'auditlog.middleware.AuditlogMiddleware',        # 2. Captura contexto
    # ... otros middlewares ...
]
```

### JWTAuthenticationMiddleware

**Ubicacion:** `store/middleware.py`

**Problema que resuelve:**
- Django REST Framework autentica JWT en la capa de **vistas**
- AuditlogMiddleware captura el usuario en la capa de **middleware**
- Sin este middleware, auditlog veria `request.user` como anonimo

**Como funciona:**

```python
class JWTAuthenticationMiddleware:
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

### AuditlogMiddleware

**Ubicacion:** `auditlog.middleware` (libreria django-auditlog)

**Que captura:**
- `actor`: Usuario autenticado (desde `request.user`)
- `remote_addr`: IP del cliente

---

## Orden de ejecucion

```
Request entrante
      │
      ▼
[AuthenticationMiddleware]     # Django: sesiones
      │
      ▼
[JWTAuthenticationMiddleware]  # Nuestro: autentica JWT
      │                         request.user = Usuario(id=1)
      ▼
[AuditlogMiddleware]           # Auditlog: captura contexto
      │                         actor = Usuario(id=1)
      │                         remote_addr = "127.0.0.1"
      ▼
[Vista/ViewSet]                # Procesa la solicitud
      │
      ▼
[Guarda en BD]                 # auditlog crea LogEntry
      │
      ▼
[Signal post_log]              # Nuestro handler verifica AuditModelConfig
      │
      ├─ is_active=True  → Log permanece
      └─ is_active=False → Log eliminado
```

---

## Uso

### Activar auditoria para un modelo

1. Ir a `/admin/audit/auditmodelconfig/`
2. Buscar el modelo (ej: `inventory | product`)
3. Marcar `is_active = True`
4. Guardar

### Desactivar auditoria para un modelo

1. Ir a `/admin/audit/auditmodelconfig/`
2. Buscar el modelo
3. Desmarcar `is_active = False`
4. Guardar

**Nota:** Los logs historicos NO se eliminan al desactivar. Solo se dejan de crear nuevos logs.

### Ver logs de auditoria

Panel de administracion:
```
http://127.0.0.1:8000/admin/auditlog/logentry/
```

---

## Consideraciones tecnicas

### Overhead

El sistema actual crea el log y luego lo elimina si `is_active=False`. Esto genera 2 operaciones de BD (INSERT + DELETE) por cada cambio en modelos desactivados.

**Alternativa:** Usar el signal `pre_log` para prevenir la creacion. Sin embargo, el enfoque actual es mas simple y el overhead es negligible para la mayoria de aplicaciones.

### Nuevos modelos

Cuando crees nuevos modelos:

```bash
python manage.py makemigrations
python manage.py migrate
```

La configuracion `AuditModelConfig` se crea **automaticamente** gracias al signal `post_migrate`. No necesitas ejecutar comandos adicionales.

Luego activa la auditoria en `/admin/audit/auditmodelconfig/` si lo deseas.
