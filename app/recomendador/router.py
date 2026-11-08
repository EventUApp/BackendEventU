"""Rutas del módulo recomendador. Cada HU añade aquí sus endpoints (ver docs/ y CLAUDE.md)."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class RecommendationInput(BaseModel):
    budget_cop: int = Field(..., ge=1_000_000, le=50_000_000)
    event_type: Literal["cumpleanos", "boda", "xv"]
    guests: int = Field(..., ge=1, le=500)


@router.post("/recommendations")
def recommendations(payload: RecommendationInput) -> RecommendationInput:
    return payload
