# Admin API

Esta API está pensada para que el frontend de Piroxeno tenga una interfaz privada
para administrar clientes, dominios, licencias y consumo.

## Seguridad actual

De momento usa un bearer token genérico:

```env
ADMIN_API_TOKEN=un_token_largo_y_aleatorio
```

Todas las llamadas admin deben enviar:

```http
Authorization: Bearer un_token_largo_y_aleatorio
```

Esto es suficiente para una primera herramienta interna, pero para producción la
mejor práctica es conectar el frontend a Supabase Auth y que el backend valide el
JWT de Supabase. Luego el backend debe consultar `app_users` para saber si el
usuario tiene rol `admin` o `user`.

## Endpoints

Listar clientes:

```http
GET /admin/clients
```

Crear cliente:

```http
POST /admin/clients
```

```json
{
  "client_slug": "nuevo_cliente",
  "name": "Nuevo Cliente",
  "title": "Asistente Nuevo Cliente",
  "allowed_origins": ["https://www.cliente.com"],
  "primary_color": "#22c55e",
  "rate_limit_per_minute": 30
}
```

Actualizar whitelist/licencia:

```http
PATCH /admin/clients/{client_slug}/config
```

```json
{
  "allowed_origins": ["https://cliente.com", "https://www.cliente.com"],
  "enabled": true,
  "rate_limit_per_minute": 30
}
```

Ver consumo:

```http
GET /admin/clients/{client_slug}/usage
```

Crear o actualizar permiso de usuario:

```http
POST /admin/users
```

```json
{
  "email": "usuario@cliente.com",
  "role": "user",
  "client_slug": "avaluos",
  "is_active": true
}
```

Para un admin global:

```json
{
  "email": "admin@piroxeno.com",
  "role": "admin",
  "client_slug": null,
  "is_active": true
}
```

## Frontend Piroxeno

Best practices:

- El frontend debe hacer login con Supabase Auth.
- No pongas `SUPABASE_SERVICE_ROLE_KEY` en el frontend nunca.
- El frontend llama a tu backend API, no directo a tablas sensibles.
- El backend valida permisos y usa `SUPABASE_SERVICE_ROLE_KEY` solo server-side.
- Roles:
  - `admin`: puede crear clientes, editar whitelist, ver consumo global y crear usuarios.
  - `user`: solo puede ver el `client_slug` asignado.
- Para el MVP puedes usar `ADMIN_API_TOKEN` solo en llamadas server-side:
  API routes, server actions, backend propio o BFF. No lo pongas en código que
  llegue al navegador, ni siquiera como variable `NEXT_PUBLIC_*`.

## Flujo recomendado

1. Admin inicia sesión en Piroxeno frontend.
2. Frontend obtiene sesión de Supabase Auth.
3. Frontend llama backend `/admin/*` con `Authorization`.
4. Backend valida rol.
5. Backend crea carpeta/config/snippet del cliente y guarda metadata en Supabase.
