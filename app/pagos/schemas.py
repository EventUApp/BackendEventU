"""Esquemas de pago. Los datos de tarjeta solo existen durante la solicitud."""

import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

CARD_NUMBER_PATTERN = re.compile(r"^[0-9]{16}$")
CARD_EXPIRY_PATTERN = re.compile(r"^(0[1-9]|1[0-2])/([0-9]{2}|[0-9]{4})$")
CARD_CVV_PATTERN = re.compile(r"^[0-9]{3,4}$")


class PaymentCardInput(BaseModel):
    number: str
    expiry: str
    cvv: str

    @field_validator("number")
    @classmethod
    def validate_number(cls, value: str) -> str:
        if not CARD_NUMBER_PATTERN.fullmatch(value):
            raise ValueError("Número de tarjeta inválido.")
        return value

    @field_validator("expiry")
    @classmethod
    def validate_expiry(cls, value: str) -> str:
        match = CARD_EXPIRY_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("Formato de vencimiento inválido.")
        month = int(value[:2])
        year_text = match.group(2)
        year = int(year_text)
        if len(year_text) == 2:
            year += 2000
        today = date.today()
        if (year, month) < (today.year, today.month):
            raise ValueError("La tarjeta está vencida.")
        return value

    @field_validator("cvv")
    @classmethod
    def validate_cvv(cls, value: str) -> str:
        if not CARD_CVV_PATTERN.fullmatch(value):
            raise ValueError("El código de seguridad debe tener 3 o 4 dígitos.")
        return value


class PaymentInput(BaseModel):
    reservation_code: str = Field(..., pattern=r"^EU-[A-Z0-9]{6}$")
    card: PaymentCardInput


class PaymentResultResponse(BaseModel):
    status: str
    reference: str
    amount_cop: int


class PaymentResponse(BaseModel):
    payment: PaymentResultResponse
    reservation_status: str
