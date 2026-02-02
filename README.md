# Inventory API

API REST para gestion de inventario con auditoria centralizada y control dinamico por modelo.

## Tecnologias

- Django 5.2
- Django REST Framework
- JWT (SimpleJWT)
- django-auditlog

## Caracteristicas principales

- CRUD completo de productos, categorias y proveedores
- Relacion ManyToMany entre productos y proveedores
- Autenticacion JWT
- **Auditoria centralizada** con control por base de datos
- Activar/desactivar tracking por modelo sin modificar codigo

## Inicio rapido

```bash
# Clonar e instalar
git clone <url>
cd HISTORIAL_V3
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configurar
cp .env.example .env
python manage.py migrate  # Crea tablas y configura auditoria automaticamente
python manage.py createsuperuser

# Ejecutar
python manage.py runserver
```

## Endpoints principales

| Metodo | URL | Descripcion |
|--------|-----|-------------|
| POST | `/api/token/` | Obtener JWT |
| POST | `/api/token/refresh/` | Refrescar JWT |
| GET/POST | `/api/categories/` | Listar/Crear categorias |
| GET/POST | `/api/suppliers/` | Listar/Crear proveedores |
| GET/POST | `/api/products/` | Listar/Crear productos |

## Documentacion

- [Instalacion](docs/instalacion.md)
- [API Endpoints](docs/api.md)
- [Sistema de Auditoria](docs/auditoria.md)
- [Configuracion de Auditoria](docs/configuracion.md)

## Estructura

```
HISTORIAL_V3/
├── store/              # Proyecto Django (settings, urls, middleware)
├── inventory/          # App de inventario (productos, categorias, proveedores)
├── audit/              # App de control de auditoria
│   ├── models.py       # AuditModelConfig (control por modelo)
│   ├── signals.py      # Filtrado de logs segun configuracion
│   └── apps.py         # Auto-configuracion via post_migrate
├── docs/               # Documentacion
├── .env.example        # Variables de entorno ejemplo
└── requirements.txt
```

## Control de Auditoria

El sistema permite activar/desactivar la auditoria por modelo desde el admin de Django:

1. Acceder a `/admin/audit/auditmodelconfig/`
2. Activar (`is_active=True`) los modelos que deseas auditar
3. Los cambios aplican inmediatamente sin reiniciar el servidor
