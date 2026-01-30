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
    "stock": 10
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
        "stock": 10
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

### Actualizar parcial

```
PATCH /api/products/{id}/
```

**Body:**
```json
{
    "price": 1200.00
}
```

### Eliminar

```
DELETE /api/products/{id}/
```