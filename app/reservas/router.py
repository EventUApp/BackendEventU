"""Rutas del módulo reservas."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.reservas.schemas import ReservationInput, ReservationResponse
from app.reservas.service import create_reservation
from app.shared.db import get_session

router = APIRouter()


@router.post("/reservations", response_model=ReservationResponse, status_code=201)
def reservations(
    payload: ReservationInput, db: Annotated[Session, Depends(get_session)]
) -> ReservationResponse:
    return create_reservation(payload, db)
