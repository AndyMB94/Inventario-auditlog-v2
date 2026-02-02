# Instalacion

## Requisitos

- Python 3.10+
- pip

## Pasos

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd HISTORIAL_V3
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copiar el archivo de ejemplo:
```bash
cp .env.example .env
```

Editar `.env` con tus valores:
```
# Django
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=1
```

### 6. Aplicar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Activar auditoria para modelos deseados

La configuracion de auditoria (`AuditModelConfig`) se crea **automaticamente** al ejecutar `migrate` gracias al signal `post_migrate`.

Por defecto, todos los modelos inician con `is_active=False` (auditoria desactivada).

1. Acceder al admin: `http://127.0.0.1:8000/admin/`
2. Ir a **Audit > Audit model configs**
3. Activar `is_active=True` en los modelos que deseas auditar (ej: `inventory.product`, `inventory.category`)

### 9. Ejecutar servidor

```bash
python manage.py runserver
```

El servidor estara disponible en `http://127.0.0.1:8000/`

---

## Verificar instalacion

1. Obtener token JWT:
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "tu_usuario", "password": "tu_password"}'
```

2. Crear un producto (con auditoria activada):
```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "category": 1, "price": 100, "stock": 10}'
```

3. Verificar log en admin: `http://127.0.0.1:8000/admin/auditlog/logentry/`
