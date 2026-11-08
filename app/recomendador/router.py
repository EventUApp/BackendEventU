"""Rutas del módulo recomendador."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.recomendador.schemas import QuoteInput, QuoteResponse, RecommendationInput, RecommendationResponse
from app.recomendador.service import get_quote, get_recommendations
from app.shared.db import get_session

router = APIRouter()


@router.post("/recommendations")
def recommendations(
    payload: RecommendationInput, db: Annotated[Session, Depends(get_session)]
) -> RecommendationResponse:
    return get_recommendations(payload.budget_cop, payload.event_type, payload.guests, db)


@router.post("/quotes")
def quotes(payload: QuoteInput, db: Annotated[Session, Depends(get_session)]) -> QuoteResponse:
    return get_quote(
        payload.budget_cop,
        payload.event_type,
        payload.guests,
        payload.service_ids,
        db,
    )
