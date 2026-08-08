from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.core.admin_auth import require_admin
from app.services.admin_service import (
    create_client,
    get_client_detail,
    get_client_usage,
    list_client_registry,
    list_clients,
    list_users,
    publish_local_clients_to_registry,
    sync_clients_from_registry,
    update_client_config,
    upsert_user,
)


router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


class CreateClientRequest(BaseModel):
    client_slug: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    name: str
    title: str | None = None
    allowed_origins: list[str] = []
    primary_color: str = "#22c55e"
    rate_limit_per_minute: int = 30


class UpdateClientConfigRequest(BaseModel):
    allowed_origins: list[str] | None = None
    enabled: bool | None = None
    rate_limit_per_minute: int | None = None
    prompt: str | None = None
    lead_columns: list[dict[str, str]] | None = None


class UpsertUserRequest(BaseModel):
    email: str
    role: str = Field(pattern=r"^(admin|user)$")
    client_slug: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")
    is_active: bool = True
    password: str | None = Field(default=None, min_length=10)


@router.get("/clients")
def admin_list_clients():
    return {"clients": list_clients()}


@router.get("/client-registry")
def admin_list_client_registry():
    return {"clients": list_client_registry()}


@router.post("/clients/sync-from-registry")
def admin_sync_clients_from_registry():
    return sync_clients_from_registry()


@router.post("/client-registry/publish-local")
def admin_publish_local_clients_to_registry():
    return publish_local_clients_to_registry()


@router.post("/clients")
def admin_create_client(body: CreateClientRequest):
    return create_client(
        client_slug=body.client_slug,
        name=body.name,
        title=body.title,
        allowed_origins=body.allowed_origins,
        primary_color=body.primary_color,
        rate_limit_per_minute=body.rate_limit_per_minute,
    )


@router.get("/clients/{client_slug}")
def admin_get_client(client_slug: str):
    return get_client_detail(client_slug)


@router.patch("/clients/{client_slug}/config")
def admin_update_client_config(client_slug: str, body: UpdateClientConfigRequest):
    return {
        "config": update_client_config(
            client_slug,
            allowed_origins=body.allowed_origins,
            enabled=body.enabled,
            rate_limit_per_minute=body.rate_limit_per_minute,
            prompt=body.prompt,
            lead_columns=body.lead_columns,
        )
    }


@router.get("/clients/{client_slug}/usage")
def admin_get_client_usage(client_slug: str):
    return get_client_usage(client_slug)


@router.get("/users")
def admin_list_users():
    return {"users": list_users()}


@router.post("/users")
def admin_upsert_user(body: UpsertUserRequest, admin_user: dict = Depends(require_admin)):
    return {
        "user": upsert_user(
            email=body.email,
            role=body.role,
            client_slug=body.client_slug,
            is_active=body.is_active,
            password=body.password,
            actor_email=admin_user.get("email"),
        )
    }
