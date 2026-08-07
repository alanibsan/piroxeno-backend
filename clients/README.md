# Clientes

Cada carpeta dentro de `clients/` representa un cliente y su configuración.

Estructura mínima:

```text
clients/<client_slug>/
  config.json
  prompt.txt
  embed.html
```

`config.json` guarda la key hasheada, dominios permitidos y rate limit.
`prompt.txt` define la personalidad, reglas e información del asistente.
`embed.html` contiene el snippet que el cliente debe pegar en su sitio web.

## Crear un cliente nuevo

```bash
python3 scripts/create_client.py nombre_cliente \
  --name "Nombre Cliente" \
  --title "Asistente Nombre Cliente" \
  --api-url "https://api.piroxeno.com" \
  --origin "https://www.cliente.com"
```

Después edita:

```text
clients/nombre_cliente/prompt.txt
```

## Dónde pegar el snippet

El cliente debe pegar el contenido de `embed.html` antes de cerrar la etiqueta
`</body>` en su sitio web.

Ejemplo:

```html
<body>
  <!-- contenido de la página -->

  <!-- pegar aquí el snippet -->
</body>
```

El valor importante es `data-client-slug`. Ese slug conecta el widget con:

- `clients/<client_slug>/prompt.txt`
- conversaciones en Supabase filtradas por `client_slug`
- memoria por `session_id`

`data-client-key` identifica al cliente. No es una contraseña secreta porque vive
en el navegador, pero evita uso casual del endpoint y debe coincidir con el hash
guardado en `config.json`.

## Seguridad por dominio

Antes de poner un cliente en producción, edita:

```text
clients/<client_slug>/config.json
```

y agrega los dominios reales donde estará instalado el widget:

```json
{
  "allowed_origins": [
    "https://cliente.com",
    "https://www.cliente.com"
  ]
}
```

Si alguien copia el snippet y lo pega en otro dominio, el backend debe rechazarlo
con `403 Origin not allowed`.
