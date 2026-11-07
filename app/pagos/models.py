"""Modelo de pagos simulados (ver docs/20261105_BD_BaseDatos_EU.md, §2.7). Nunca datos de tarjeta."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    reservation_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), ForeignKey("reservations.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(Text)
    amount_cop: Mapped[int] = mapped_column(Integer)
    reference: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
