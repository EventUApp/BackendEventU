"""Esquemas de creación de reservas."""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}$"
)
PHONE_PATTERN = re.compile(r"^[0-9]{10}$")


class ReservationCustomerInput(BaseModel):
    name: str = Field(..., max_length=100)
    email: str = Field(..., max_length=254)
    phone: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Nombre requerido.")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Formato de correo inválido.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not PHONE_PATTERN.fullmatch(value):
            raise ValueError("El teléfono debe tener 10 dígitos.")
        return value


class ReservationInput(BaseModel):
    budget_cop: int | None = Field(default=None, ge=1_000_000, le=50_000_000)
    event_type: Literal["cumpleanos", "boda", "xv"]
    guests: int = Field(..., ge=1, le=500)
    modality: Literal["ahorro", "equilibrado", "premium", "personalizado"]
    service_ids: list[str]
    expected_total_cop: int = Field(..., ge=0)
    customer: ReservationCustomerInput
    event_date: date

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: date) -> date:
        if value <= date.today():
            raise ValueError("La fecha del evento debe ser futura.")
        return value


class ReservationCustomerResponse(BaseModel):
    name: str
    email: str
    phone: str


class ReservationItemResponse(BaseModel):
    service_id: str
    category: str
    service_name: str
    provider_name: str
    price_model: str
    unit_price_cop: int
    cost_cop: int


class ReservationResponse(BaseModel):
    code: str
    status: str
    total_cop: int
    items: list[ReservationItemResponse]
    customer: ReservationCustomerResponse
    event_date: date
