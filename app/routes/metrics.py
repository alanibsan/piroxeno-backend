from fastapi import APIRouter, Depends
from app.core.auth import authenticate_client
from app.services.metrics_service import get_client_metrics

router = APIRouter()


@router.get("/metrics")
def metrics(client: dict = Depends(authenticate_client)):
    client_slug = client["slug"]
    return get_client_metrics(client_slug)
