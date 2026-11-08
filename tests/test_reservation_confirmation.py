import uuid
from datetime import date, timedelta

import pytest

from app.pagos.models import Payment
from app.reservas.models import Reservation, ReservationItem


def _create_reservation(session, code: str, status: str) -> None:
    reservation_id = str(uuid.uuid4())
    session.add(
        Reservation(
            id=reservation_id,
            code=code,
            status=status,
            event_type="boda",
            guests=50,
            budget_cop=1_000_000,
            modality="equilibrado",
            total_cop=125_000,
            customer_name="Ana Organiza",
            customer_email="ana@example.invalid",
            customer_phone="3001234567",
            event_date=date.today() + timedelta(days=30),
        )
    )
    session.add(
        ReservationItem(
            reservation_id=reservation_id,
            category="espacio",
            service_id=None,
            service_name="Salón de eventos",
            provider_name="Eventos Cali",
            price_model="fijo",
            unit_price_cop=125_000,
            cost_cop=125_000,
        )
    )
    session.flush()
    if status == "pagada":
        session.add(
            Payment(
                id=str(uuid.uuid4()),
                reservation_id=reservation_id,
                status="aprobado",
                amount_cop=125_000,
                reference="SIM-CONFIRMACION",
            )
        )
    session.commit()


def test_get_reservation_returns_confirmation_for_paid_reservation(client, session):
    _create_reservation(session, "EU-ABC123", "pagada")

    response = client.get("/api/v1/reservations/EU-ABC123")

    assert response.status_code == 200
    assert response.json() == {
        "code": "EU-ABC123",
        "status": "pagada",
        "modality": "equilibrado",
        "total_cop": 125_000,
        "items": [
            {
                "service_id": None,
                "category": "espacio",
                "service_name": "Salón de eventos",
                "provider_name": "Eventos Cali",
                "price_model": "fijo",
                "unit_price_cop": 125_000,
                "cost_cop": 125_000,
            }
        ],
        "customer": {
            "name": "Ana Organiza",
            "email": "ana@example.invalid",
            "phone": "3001234567",
        },
        "event_date": (date.today() + timedelta(days=30)).isoformat(),
        "payment": {"status": "aprobado", "reference": "SIM-CONFIRMACION"},
    }


@pytest.mark.parametrize("status", ["creada", "pago_rechazado", "cancelada"])
def test_get_reservation_hides_confirmation_until_paid(client, session, status):
    _create_reservation(session, "EU-ABC123", status)

    response = client.get("/api/v1/reservations/EU-ABC123")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"
    assert "customer" not in response.json()


def test_get_reservation_returns_not_found_for_unknown_code(client):
    response = client.get("/api/v1/reservations/EU-ZZZ999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "No encontramos una reserva con ese número."


@pytest.mark.parametrize("code", ["invalid", "EU-ABC12", "EU-ABC12!"])
def test_get_reservation_validates_code_format(client, code):
    response = client.get(f"/api/v1/reservations/{code}")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["fields"]["code"] == "El número de reserva no es válido."
