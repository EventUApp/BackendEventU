"""Puerto PaymentGateway y su implementación simulada (ADR-05). La completa HU_EU_03_10."""

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

APPROVED_TEST_CARD = "4242424242424242"  # Propuesto (RN-17, PB-07)
DECLINED_TEST_CARD = "4000000000000002"  # Propuesto (RN-17, PB-07)


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


class SimulatedGateway:
    def charge(self, reservation_code: str, amount_cop: int, card: CardInput) -> PaymentResult:
        del reservation_code, amount_cop
        return PaymentResult(
            approved=card.number == APPROVED_TEST_CARD,
            reference=f"SIM-{uuid4().hex[:12].upper()}",
        )
