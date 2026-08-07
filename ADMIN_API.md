# Admin API

Esta API está pensada para que el frontend de Piroxeno tenga una interfaz privada
para administrar clientes, dominios, licencias y consumo.

## Seguridad actual

El portal usa login con email y contraseña:

```http
POST /auth/login
```

```json
{
  "email": "admin@piroxeno.com",
  "password": "una_password_larga"
}
```

La respuesta incluye un token temporal de sesión. El frontend debe enviar:

```http
Authorization: Bearer token_de_sesion
```

`ADMIN_API_TOKEN` queda solo como llave bootstrap/server-side para crear la
primera cuenta admin o hacer mantenimiento desde scripts internos:

```env
ADMIN_API_TOKEN=un_token_largo_y_aleatorio
```

No pegues `ADMIN_API_TOKEN` en el navegador ni en variables `VITE_*`.

Para producción define también:

```env
ADMIN_SESSION_SECRET=otro_secreto_largo_y_aleatorio
```

Si no lo defines, el backend usa `SUPABASE_SERVICE_ROLE_KEY` como fallback
server-side para firmar sesiones. Aun así es mejor tener `ADMIN_SESSION_SECRET`
dedicado.

Corre `app/migrations/004_admin_password_auth.sql` en Supabase antes de crear
usuarios con contraseña.

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

Sincronizar clientes desde Supabase hacia las carpetas locales:

```http
POST /admin/clients/sync-from-registry
```

Publicar carpetas locales hacia Supabase:

```http
POST /admin/client-registry/publish-local
```

O desde dev/local:

```bash
venv/bin/python scripts/sync_clients_from_registry.py
```

Para subir los clientes locales actuales al registry:

```bash
venv/bin/python scripts/publish_local_clients_to_registry.py
```

Para automatizarlo diario en tu máquina/dev server, programa ese comando con
cron, launchd, GitHub Actions o el scheduler que uses. Producción guarda cada
cliente nuevo o cambio de configuración en `client_registry`, y dev puede
regenerar sus carpetas desde ahí.

Crear o actualizar permiso de usuario:

```http
POST /admin/users
```

```json
{
  "email": "usuario@cliente.com",
  "role": "user",
  "client_slug": "avaluos",
  "is_active": true,
  "password": "password_larga_temporal"
}
```

Para un admin global:

```json
{
  "email": "admin@piroxeno.com",
  "role": "admin",
  "client_slug": null,
  "is_active": true,
  "password": "password_larga_temporal"
}
```

## Frontend Piroxeno

Best practices:

- El frontend debe hacer login contra `/auth/login`.
- No pongas `SUPABASE_SERVICE_ROLE_KEY` en el frontend nunca.
- No pongas `ADMIN_API_TOKEN` en el frontend.
- El frontend llama a tu backend API, no directo a tablas sensibles.
- El backend valida permisos y usa `SUPABASE_SERVICE_ROLE_KEY` solo server-side.
- Roles:
  - `admin`: puede crear clientes, editar whitelist, ver consumo global y crear usuarios.
  - `user`: solo puede ver el `client_slug` asignado.

## Flujo recomendado

1. Admin inicia sesión en Piroxeno frontend con email/password.
2. Frontend guarda el token temporal en `sessionStorage`.
3. Frontend llama backend `/admin/*` con `Authorization`.
4. Backend valida rol.
5. Backend crea carpeta/config/snippet del cliente y guarda metadata en Supabase.
