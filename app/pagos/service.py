"""Reglas de negocio para el pago simulado."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AppError
from app.pagos.gateway import CardInput, PaymentGateway, SimulatedGateway
from app.pagos.repository import get_reservation_for_update, save_payment
from app.pagos.schemas import PaymentInput, PaymentResponse


def process_payment(
    payload: PaymentInput, session: Session, gateway: PaymentGateway | None = None
) -> PaymentResponse:
    reservation = get_reservation_for_update(session, payload.reservation_code)
    if reservation is None:
        raise AppError("NOT_FOUND", "No encontramos la reserva.", 404)
    if reservation.status == "pagada":
        raise AppError("ALREADY_PAID", "La reserva ya fue pagada.")
    if reservation.status not in {"creada", "pago_rechazado"}:
        raise AppError("INVALID_STATE", "La reserva no admite pagos.")

    payment_gateway = gateway or SimulatedGateway()
    result = payment_gateway.charge(
        reservation.code,
        reservation.total_cop,
        CardInput(
            number=payload.card.number,
            expiry=payload.card.expiry,
            cvv=payload.card.cvv,
        ),
    )
    status = "aprobado" if result.approved else "rechazado"
    try:
        payment = save_payment(
            session,
            reservation,
            status,
            reservation.total_cop,
            result.reference,
        )
    except IntegrityError:
        current_reservation = get_reservation_for_update(session, payload.reservation_code)
        if current_reservation is not None and current_reservation.status == "pagada":
            raise AppError("ALREADY_PAID", "La reserva ya fue pagada.") from None
        raise
    return PaymentResponse(payment=payment, reservation_status=reservation.status)
