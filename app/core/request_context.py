# app/core/request_context.py

from contextvars import ContextVar

# Variables globales de contexto
_request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default=None)
_client_slug_ctx_var: ContextVar[str] = ContextVar("client_slug", default=None)


# -------- Request ID --------

def set_request_id(request_id: str):
    _request_id_ctx_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx_var.get()


# -------- Client Slug --------

def set_client_slug(slug: str):
    _client_slug_ctx_var.set(slug)


def get_client_slug() -> str | None:
    return _client_slug_ctx_var.get()
