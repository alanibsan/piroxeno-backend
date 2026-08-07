import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path("clients")
MAX_MESSAGES = 20


def _session_path(client_slug: str, session_id: str) -> Path:
    return BASE_DIR / client_slug / "sessions" / f"{session_id}.json"


def load_messages(client_slug: str, session_id: str) -> list[dict]:
    path = _session_path(client_slug, session_id)

    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return []

    return messages[-MAX_MESSAGES:]


def save_messages(client_slug: str, session_id: str, messages: list[dict]) -> None:
    path = _session_path(client_slug, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "session_id": session_id,
        "client_slug": client_slug,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages[-MAX_MESSAGES:],
    }

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def reset_session(client_slug: str, session_id: str) -> None:
    path = _session_path(client_slug, session_id)
    if path.exists():
        path.unlink()
