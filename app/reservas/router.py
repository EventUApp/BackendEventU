"""Rutas del módulo reservas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.reservas.schemas import (
    RESERVATION_CODE_PATTERN,
    ReservationConfirmationResponse,
    ReservationInput,
    ReservationResponse,
)
from app.reservas.service import create_reservation, get_reservation_confirmation
from app.shared.db import get_session

router = APIRouter()


@router.get("/reservations/{code}", response_model=ReservationConfirmationResponse)
def reservation_confirmation(
    code: Annotated[str, Path(pattern=RESERVATION_CODE_PATTERN)],
    db: Annotated[Session, Depends(get_session)],
) -> ReservationConfirmationResponse:
    return get_reservation_confirmation(code, db)


@router.post("/reservations", response_model=ReservationResponse, status_code=201)
def reservations(
    payload: ReservationInput, db: Annotated[Session, Depends(get_session)]
) -> ReservationResponse:
    return create_reservation(payload, db)
