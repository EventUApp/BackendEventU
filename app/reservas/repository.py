"""Persistencia de reservas y su copia de servicios."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.pagos.models import Payment
from app.reservas.models import Reservation, ReservationItem


def reservation_code_exists(session: Session, code: str) -> bool:
    return session.query(Reservation.id).filter(Reservation.code == code).first() is not None


def save_reservation(session: Session, reservation: Reservation, items: list[ReservationItem]) -> None:
    try:
        session.add(reservation)
        session.add_all(items)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


def get_reservation_by_code(session: Session, code: str) -> Reservation | None:
    return session.scalar(select(Reservation).where(Reservation.code == code))


def get_reservation_items(session: Session, reservation_id: str) -> list[ReservationItem]:
    return list(
        session.scalars(
            select(ReservationItem)
            .where(ReservationItem.reservation_id == reservation_id)
            .order_by(ReservationItem.category)
        )
    )


def get_approved_payment(session: Session, reservation_id: str) -> Payment | None:
    return session.scalar(
        select(Payment)
        .where(Payment.reservation_id == reservation_id, Payment.status == "aprobado")
        .order_by(Payment.created_at.desc())
    )
