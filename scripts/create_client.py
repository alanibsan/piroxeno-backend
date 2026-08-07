from pathlib import Path
import argparse
import hashlib
import json
import re
import secrets


CLIENTS_DIR = Path("clients")
DEFAULT_API_URL = "https://api.piroxeno.com"


PROMPT_TEMPLATE = """Eres el asistente del sitio web de {name}.

Tu función es:
- Responder dudas de visitantes y clientes
- Capturar datos importantes para seguimiento
- Mantener continuidad dentro de la misma conversación

Reglas:
- Responde de forma clara, breve y profesional
- No repitas preguntas si el usuario ya dio la información
- Si falta información, pide solo el siguiente dato más importante
- No inventes precios, tiempos, requisitos ni disponibilidad
- Si no sabes algo, di que no dispones de esa información
"""


def validate_slug(slug: str):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", slug):
        raise ValueError("El slug solo puede usar letras, números, guion y guion bajo.")


def hash_key(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def embed_code(
    slug: str,
    api_url: str,
    client_key: str,
    title: str | None,
    primary_color: str,
):
    return f"""<!-- Piroxeno AI Chatbot - {slug} -->
<!-- Pegar este código antes de cerrar </body> en la página del cliente. -->
<script
  src="{api_url.rstrip("/")}/static/widget.js"
  data-api-url="{api_url.rstrip("/")}"
  data-client-slug="{slug}"
  data-client-key="{client_key}"
  data-title="{title or "AI Assistant"}"
  data-primary-color="{primary_color}"
  async>
</script>
"""


def client_config(client_key: str, allowed_origins: list[str], rate_limit: int):
    return {
        "enabled": True,
        "embed_key_hash": hash_key(client_key),
        "allowed_origins": allowed_origins,
        "rate_limit_per_minute": rate_limit,
    }


def create_client(
    slug: str,
    name: str | None,
    api_url: str,
    title: str | None,
    primary_color: str,
    allowed_origins: list[str],
    rate_limit: int,
    overwrite_prompt: bool,
):
    validate_slug(slug)

    client_dir = CLIENTS_DIR / slug
    client_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = client_dir / "prompt.txt"
    if overwrite_prompt or not prompt_path.exists():
        prompt_path.write_text(
            PROMPT_TEMPLATE.format(name=name or slug),
            encoding="utf-8",
        )

    client_key = secrets.token_urlsafe(32)

    config_path = client_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(
            json.dumps(
                client_config(client_key, allowed_origins, rate_limit),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        existing_hash = config.get("embed_key_hash")
        if existing_hash:
            raise ValueError(
                "config.json ya existe. No puedo regenerar embed.html sin la key pública original."
            )

    embed_path = client_dir / "embed.html"
    embed_path.write_text(
        embed_code(slug, api_url, client_key, title or name, primary_color),
        encoding="utf-8",
    )

    print(f"Cliente listo: {client_dir}")
    print(f"Prompt: {prompt_path}")
    print(f"Config: {config_path}")
    print(f"Embed: {embed_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Crea la carpeta de un cliente con prompt.txt y embed.html."
    )
    parser.add_argument("slug", help="Identificador del cliente, por ejemplo avaluos")
    parser.add_argument("--name", help="Nombre visible del cliente")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--title", help="Título mostrado en el widget")
    parser.add_argument("--primary-color", default="#22c55e")
    parser.add_argument(
        "--origin",
        action="append",
        default=[],
        help="Dominio permitido del cliente. Puede repetirse.",
    )
    parser.add_argument("--rate-limit", type=int, default=30)
    parser.add_argument(
        "--overwrite-prompt",
        action="store_true",
        help="Sobrescribe prompt.txt si ya existe.",
    )

    args = parser.parse_args()
    create_client(
        args.slug,
        args.name,
        args.api_url,
        args.title,
        args.primary_color,
        args.origin,
        args.rate_limit,
        args.overwrite_prompt,
    )


if __name__ == "__main__":
    main()
