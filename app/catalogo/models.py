"""Modelos del catálogo (docs/20261105_BD_BaseDatos_EU.md §2). Las restricciones las impone la migración."""

from datetime import date, datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base


class Provider(Base):
    __tablename__ = "providers"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    neighborhood: Mapped[str] = mapped_column(Text)
    municipality: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    featured: Mapped[bool] = mapped_column(Boolean, server_default=text("FALSE"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))


class ProviderVerification(Base):
    __tablename__ = "provider_verifications"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    check_type: Mapped[str] = mapped_column(Text)
    checked_on: Mapped[date]
    notes: Mapped[str] = mapped_column(Text)


class ProviderImage(Base):
    __tablename__ = "provider_images"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(Text)
    alt_text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)


class ProviderReview(Base):
    __tablename__ = "provider_reviews"
    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    author_name: Mapped[str] = mapped_column(Text)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    reviewed_on: Mapped[date]


class Service(Base):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id", ondelete="RESTRICT"))
    category: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    price_model: Mapped[str] = mapped_column(Text)
    base_price_cop: Mapped[int] = mapped_column(Integer)
    min_guests: Mapped[int] = mapped_column(Integer)
    max_guests: Mapped[int] = mapped_column(Integer)


class ServiceEventType(Base):
    __tablename__ = "service_event_types"
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, primary_key=True)
