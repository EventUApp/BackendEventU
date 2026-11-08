"""Esquemas de entrada y salida del endpoint de recomendaciones."""

from typing import Literal

from pydantic import BaseModel, Field


class RecommendationInput(BaseModel):
    budget_cop: int = Field(..., ge=1_000_000, le=50_000_000)
    event_type: Literal["cumpleanos", "boda", "xv"]
    guests: int = Field(..., ge=1, le=500)


class RecommendationItemResponse(BaseModel):
    service_id: str
    name: str
    provider_id: str
    provider_name: str
    verification_status: str
    cost_cop: int


class RecommendationBreakdownResponse(BaseModel):
    category: str
    subtotal_cop: int
    items: list[RecommendationItemResponse]


class RecommendationPackageResponse(BaseModel):
    modality: str
    total_cop: int
    remaining_cop: int
    breakdown: list[RecommendationBreakdownResponse]


class RecommendationUnavailableResponse(BaseModel):
    modality: str
    cause: str


class RecommendationResponse(BaseModel):
    packages: list[RecommendationPackageResponse]
    unavailable: list[RecommendationUnavailableResponse]
