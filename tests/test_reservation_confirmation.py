import uuid
from datetime import date, timedelta

import pytest

from app.pagos.gateway import APPROVED_TEST_CARD
from app.pagos.models import Payment
from app.reservas.models import Reservation, ReservationItem
from seed.load import load_seed


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


def test_recommendation_reservation_approved_payment_and_confirmation_flow(client, session):
    load_seed(session)
    recommendation_response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 10_000_000, "event_type": "boda", "guests": 80},
    )
    assert recommendation_response.status_code == 200
    package = recommendation_response.json()["packages"][1]
    service_ids = [item["service_id"] for category in package["breakdown"] for item in category["items"]]
    customer = {
        "name": "Organizador de prueba",
        "email": "organizador@example.invalid",
        "phone": "3001234567",
    }
    event_date = (date.today() + timedelta(days=30)).isoformat()

    reservation_response = client.post(
        "/api/v1/reservations",
        json={
            "budget_cop": 10_000_000,
            "event_type": "boda",
            "guests": 80,
            "modality": package["modality"],
            "service_ids": service_ids,
            "expected_total_cop": package["total_cop"],
            "customer": customer,
            "event_date": event_date,
        },
    )
    assert reservation_response.status_code == 201
    reservation = reservation_response.json()

    payment_response = client.post(
        "/api/v1/payments",
        json={
            "reservation_code": reservation["code"],
            "card": {"number": APPROVED_TEST_CARD, "expiry": "12/30", "cvv": "123"},
        },
    )
    assert payment_response.status_code == 200
    payment = payment_response.json()
    assert payment["payment"]["status"] == "aprobado"
    assert payment["payment"]["amount_cop"] == package["total_cop"]
    assert payment["reservation_status"] == "pagada"

    confirmation_response = client.get(f"/api/v1/reservations/{reservation['code']}")

    assert confirmation_response.status_code == 200
    confirmation = confirmation_response.json()
    assert set(confirmation) == {
        "code",
        "status",
        "modality",
        "total_cop",
        "items",
        "customer",
        "event_date",
        "payment",
    }
    assert confirmation["code"] == reservation["code"]
    assert confirmation["status"] == "pagada"
    assert confirmation["modality"] == package["modality"]
    assert confirmation["total_cop"] == package["total_cop"]
    assert sorted(confirmation["items"], key=lambda item: item["category"]) == sorted(
        reservation["items"], key=lambda item: item["category"]
    )
    assert confirmation["customer"] == customer
    assert confirmation["event_date"] == event_date
    assert confirmation["payment"] == {
        "status": payment["payment"]["status"],
        "reference": payment["payment"]["reference"],
    }
    assert set(confirmation["payment"]) == {"status", "reference"}
    assert APPROVED_TEST_CARD not in confirmation_response.text
    assert "12/30" not in confirmation_response.text


@pytest.mark.parametrize("status", ["creada", "pago_rechazado", "cancelada"])
def test_get_reservation_hides_confirmation_until_paid(client, session, status):
    _create_reservation(session, "EU-ABC123", status)

    response = client.get("/api/v1/reservations/EU-ABC123")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE"
    assert "customer" not in response.json()


def test_get_reservation_requires_approved_payment_record(client, session):
    _create_reservation(session, "EU-ABC123", "creada")
    session.execute(
        Reservation.__table__.update().where(Reservation.code == "EU-ABC123").values(status="pagada")
    )
    session.commit()

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
