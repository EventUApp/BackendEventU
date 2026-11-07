"""Modelos de reservas (ver docs/20261105_BD_BaseDatos_EU.md, §2.5 y §2.6)."""

from datetime import date, datetime

from sqlalchemy import ForeignKey, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base


class Reservation(Base):
    __tablename__ = "reservations"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)  # la app lo genera (uuid4)
    code: Mapped[str] = mapped_column(Text, unique=True)
    status: Mapped[str] = mapped_column(Text, default="creada")
    event_type: Mapped[str] = mapped_column(Text)
    guests: Mapped[int] = mapped_column(Integer)
    budget_cop: Mapped[int | None] = mapped_column(Integer)  # opcional en «Mi evento» (RN-22)
    modality: Mapped[str] = mapped_column(Text)  # ahorro | equilibrado | premium | personalizado (RN-21)
    total_cop: Mapped[int] = mapped_column(Integer)
    customer_name: Mapped[str] = mapped_column(Text)
    customer_email: Mapped[str] = mapped_column(Text)
    customer_phone: Mapped[str] = mapped_column(Text)
    event_date: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))


class ReservationItem(Base):
    __tablename__ = "reservation_items"
    reservation_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("reservations.id", ondelete="CASCADE"), primary_key=True
    )
    category: Mapped[str] = mapped_column(Text, primary_key=True)
    service_id: Mapped[str | None] = mapped_column(ForeignKey("services.id", ondelete="SET NULL"))
    service_name: Mapped[str] = mapped_column(Text)
    provider_name: Mapped[str] = mapped_column(Text)
    price_model: Mapped[str] = mapped_column(Text)
    unit_price_cop: Mapped[int] = mapped_column(Integer)
    cost_cop: Mapped[int] = mapped_column(Integer)
