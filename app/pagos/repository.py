"""Lectura y persistencia de pagos y estados de reserva."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.pagos.models import Payment
from app.pagos.schemas import PaymentResultResponse
from app.reservas.models import Reservation


def get_reservation_for_update(session: Session, code: str) -> Reservation | None:
    return session.scalar(select(Reservation).where(Reservation.code == code).with_for_update())


def save_payment(
    session: Session,
    reservation: Reservation,
    status: str,
    amount_cop: int,
    reference: str,
) -> PaymentResultResponse:
    payment = Payment(
        id=str(uuid.uuid4()),
        reservation_id=reservation.id,
        status=status,
        amount_cop=amount_cop,
        reference=reference,
    )
    reservation.status = "pagada" if status == "aprobado" else "pago_rechazado"
    reservation.updated_at = datetime.now(UTC)
    try:
        session.add(payment)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    return PaymentResultResponse(status=status, reference=reference, amount_cop=amount_cop)
