"""Puerto PaymentGateway y su implementación simulada (ADR-05). La completa HU_EU_03_10."""

from dataclasses import dataclass
from typing import Protocol

APPROVED_TEST_CARD = "4242424242424242"  # Propuesto (RN-17, PB-07)


@dataclass(frozen=True)
class CardInput:
    number: str
    expiry: str
    cvv: str


@dataclass(frozen=True)
class PaymentResult:
    approved: bool
    reference: str


class PaymentGateway(Protocol):
    def charge(self, reservation_code: str, amount_cop: int, card: CardInput) -> PaymentResult: ...
