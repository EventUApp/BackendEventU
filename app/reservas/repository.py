"""Persistencia de reservas y su copia de servicios."""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

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
