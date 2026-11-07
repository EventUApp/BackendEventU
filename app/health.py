"""GET /api/v1/health: chequeo de Render y 'despertar' el servicio antes de la demo."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
