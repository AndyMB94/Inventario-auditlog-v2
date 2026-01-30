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

### 3. Auto-registro con serialize_data

**Ubicacion:** `audit/apps.py`

```python
class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        import audit.signals

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

**Por que es necesario:**
- `AUDITLOG_INCLUDE_ALL_MODELS = True` registra modelos sin `serialize_data`
- Este codigo re-registra todos los modelos con `serialize_data=True`
- Asi se guarda una copia completa del objeto en cada log

### 4. Comando de Inicializacion

**Ubicacion:** `audit/management/commands/init_audit_models.py`

```bash
python manage.py init_audit_models
```

Crea registros `AuditModelConfig` para todos los `ContentType` existentes con `is_active=False` por defecto.

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
| `action` | Tipo de accion (0=CREATE, 1=UPDATE, 2=DELETE) |
| `timestamp` | Fecha y hora de la accion |
| `remote_addr` | IP del cliente |
| `changes` | Cambios realizados en formato JSON |
| `serialized_data` | Copia completa del objeto (habilitado via apps.py) |

## Ejemplo de registro

```json
{
    "id": 1,
    "actor_id": 1,
    "actor_email": "admin@admin.com",
    "action": 1,
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

Cuando crees nuevos modelos, ejecuta:

```bash
python manage.py init_audit_models
```

Esto creara la configuracion para los nuevos `ContentType`.
