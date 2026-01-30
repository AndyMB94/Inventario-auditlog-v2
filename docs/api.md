# API Endpoints

## Autenticacion

Todos los endpoints (excepto `/api/token/`) requieren autenticacion JWT.

Header requerido:
```
Authorization: Bearer <access_token>
```

### Obtener Token

```
POST /api/token/
```

**Body:**
```json
{
    "username": "admin",
    "password": "tu_password"
}
```

**Respuesta:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1Qi...",
    "access": "eyJ0eXAiOiJKV1Qi..."
}
```

### Refrescar Token

```
POST /api/token/refresh/
```

**Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1Qi..."
}
```

---

## Categorias

### Listar

```
GET /api/categories/
```

### Crear

```
POST /api/categories/
```

**Body:**
```json
{
    "name": "Electronicos"
}
```

**Respuesta:**
```json
{
    "message": "Categoria creada exitosamente",
    "data": {
        "id": 1,
        "name": "Electronicos"
    }
}
```

### Obtener

```
GET /api/categories/{id}/
```

### Actualizar

```
PUT /api/categories/{id}/
```

### Actualizar parcial

```
PATCH /api/categories/{id}/
```

### Eliminar

```
DELETE /api/categories/{id}/
```

---

## Proveedores (Suppliers)

### Listar

```
GET /api/suppliers/
```

### Crear

```
POST /api/suppliers/
```

**Body:**
```json
{
    "name": "Tech Distribuidora",
    "email": "ventas@techdist.com",
    "phone": "999888777",
    "address": "Av. Industrial 123",
    "contact_person": "Juan Perez"
}
```

**Respuesta:**
```json
{
    "message": "Proveedor creado exitosamente",
    "data": {
        "id": 1,
        "name": "Tech Distribuidora",
        "email": "ventas@techdist.com",
        "phone": "999888777",
        "address": "Av. Industrial 123",
        "contact_person": "Juan Perez"
    }
}
```

### Obtener

```
GET /api/suppliers/{id}/
```

### Actualizar

```
PUT /api/suppliers/{id}/
```

**Body:**
```json
{
    "name": "Tech Distribuidora SAC",
    "email": "ventas@techdist.com",
    "phone": "999888777",
    "address": "Av. Industrial 456",
    "contact_person": "Juan Perez"
}
```

### Actualizar parcial

```
PATCH /api/suppliers/{id}/
```

**Body:**
```json
{
    "phone": "999000111"
}
```

### Eliminar

```
DELETE /api/suppliers/{id}/
```

---

## Productos

### Listar

```
GET /api/products/
```

### Crear

```
POST /api/products/
```

**Body:**
```json
{
    "name": "Laptop HP",
    "category": 1,
    "price": 1500.00,
    "stock": 10,
    "suppliers": [1, 2]
}
```

**Respuesta:**
```json
{
    "message": "Producto creado exitosamente",
    "data": {
        "id": 1,
        "name": "Laptop HP",
        "category": 1,
        "category_name": "Electronicos",
        "price": "1500.00",
        "stock": 10,
        "suppliers": [1, 2],
        "suppliers_detail": [
            {"id": 1, "name": "Tech Distribuidora"},
            {"id": 2, "name": "Importaciones ABC"}
        ]
    }
}
```

### Obtener

```
GET /api/products/{id}/
```

### Actualizar

```
PUT /api/products/{id}/
```

**Body:**
```json
{
    "name": "Laptop HP Pavilion",
    "category": 1,
    "price": 1600.00,
    "stock": 15,
    "suppliers": [1]
}
```

### Actualizar parcial

```
PATCH /api/products/{id}/
```

**Body:**
```json
{
    "price": 1200.00,
    "stock": 20
}
```

### Eliminar

```
DELETE /api/products/{id}/
```

---

## Resumen de Endpoints

| Metodo | URL | Descripcion |
|--------|-----|-------------|
| POST | `/api/token/` | Obtener JWT |
| POST | `/api/token/refresh/` | Refrescar JWT |
| GET | `/api/categories/` | Listar categorias |
| POST | `/api/categories/` | Crear categoria |
| GET | `/api/categories/{id}/` | Obtener categoria |
| PUT | `/api/categories/{id}/` | Actualizar categoria |
| PATCH | `/api/categories/{id}/` | Actualizar parcial categoria |
| DELETE | `/api/categories/{id}/` | Eliminar categoria |
| GET | `/api/suppliers/` | Listar proveedores |
| POST | `/api/suppliers/` | Crear proveedor |
| GET | `/api/suppliers/{id}/` | Obtener proveedor |
| PUT | `/api/suppliers/{id}/` | Actualizar proveedor |
| PATCH | `/api/suppliers/{id}/` | Actualizar parcial proveedor |
| DELETE | `/api/suppliers/{id}/` | Eliminar proveedor |
| GET | `/api/products/` | Listar productos |
| POST | `/api/products/` | Crear producto |
| GET | `/api/products/{id}/` | Obtener producto |
| PUT | `/api/products/{id}/` | Actualizar producto |
| PATCH | `/api/products/{id}/` | Actualizar parcial producto |
| DELETE | `/api/products/{id}/` | Eliminar producto |
