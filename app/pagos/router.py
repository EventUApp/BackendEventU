"""Rutas del módulo pagos."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.pagos.schemas import PaymentInput, PaymentResponse
from app.pagos.service import process_payment
from app.shared.db import get_session

router = APIRouter()


@router.post("/payments", response_model=PaymentResponse)
def payments(payload: PaymentInput, db: Annotated[Session, Depends(get_session)]) -> PaymentResponse:
    return process_payment(payload, db)
