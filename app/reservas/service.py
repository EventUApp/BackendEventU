"""Reglas de negocio para crear reservas."""

import secrets
import string
import uuid
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.catalogo.service import EligibleService, get_eligible_services
from app.errors import AppError
from app.reservas.models import Reservation, ReservationItem
from app.reservas.repository import (
    get_approved_payment,
    get_reservation_by_code,
    get_reservation_items,
    reservation_code_exists,
    save_reservation,
)
from app.reservas.schemas import (
    ReservationConfirmationResponse,
    ReservationCustomerInput,
    ReservationCustomerResponse,
    ReservationInput,
    ReservationItemResponse,
    ReservationPaymentResponse,
    ReservationResponse,
)
from app.shared.money import cost_for_guests

RESERVATION_CODE_PREFIX = "EU-"
RESERVATION_CODE_LENGTH = 6
RESERVATION_CODE_ALPHABET = string.ascii_uppercase + string.digits
RESERVATION_CODE_ATTEMPTS = 10
REQUIRED_CATEGORIES = ("espacio", "alimentacion", "decoracion")
RESERVATION_FAILURE_MESSAGE = "No fue posible crear la reserva. Revise su evento e intente nuevamente."


def _reservation_code() -> str:
    suffix = "".join(secrets.choice(RESERVATION_CODE_ALPHABET) for _ in range(RESERVATION_CODE_LENGTH))
    return f"{RESERVATION_CODE_PREFIX}{suffix}"


def _invalid_services(message: str) -> AppError:
    return AppError("VALIDATION_ERROR", RESERVATION_FAILURE_MESSAGE, 422, {"service_ids": message})


def _response(
    reservation: Reservation,
    customer: ReservationCustomerInput,
    event_date: date,
    services: tuple[EligibleService, ...],
    costs: dict[str, int],
) -> ReservationResponse:
    items = [
        ReservationItemResponse(
            service_id=service.id,
            category=service.category,
            service_name=service.name,
            provider_name=service.provider_name,
            price_model=service.price_model,
            unit_price_cop=service.base_price_cop,
            cost_cop=costs[service.id],
        )
        for service in services
    ]
    return ReservationResponse(
        code=reservation.code,
        status=reservation.status,
        total_cop=reservation.total_cop,
        items=items,
        customer=ReservationCustomerResponse(name=customer.name, email=customer.email, phone=customer.phone),
        event_date=event_date,
    )


def create_reservation(payload: ReservationInput, session: Session) -> ReservationResponse:
    if len(set(payload.service_ids)) != len(payload.service_ids):
        raise _invalid_services("No se puede incluir el mismo servicio más de una vez.")

    services = get_eligible_services(payload.service_ids, payload.event_type, payload.guests, session)
    services_by_id = {service.id: service for service in services}
    if len(services_by_id) != len(payload.service_ids):
        raise _invalid_services(
            "Uno o más servicios no están disponibles para el tipo de evento o número de invitados."
        )

    categories = [service.category for service in services]
    if len(set(categories)) != len(categories):
        raise _invalid_services("Solo se permite un servicio por rubro.")

    missing_categories = [category for category in REQUIRED_CATEGORIES if category not in categories]
    if missing_categories:
        raise _invalid_services(RESERVATION_FAILURE_MESSAGE)

    costs = {
        service.id: cost_for_guests(service.price_model, service.base_price_cop, payload.guests)
        for service in services
    }
    total_cop = sum(costs.values())
    if total_cop != payload.expected_total_cop:
        raise AppError("TOTAL_MISMATCH", RESERVATION_FAILURE_MESSAGE)
    if payload.budget_cop is not None and total_cop > payload.budget_cop:
        raise AppError("BUDGET_EXCEEDED", RESERVATION_FAILURE_MESSAGE)

    for _ in range(RESERVATION_CODE_ATTEMPTS):
        code = _reservation_code()
        if reservation_code_exists(session, code):
            continue

        reservation = Reservation(
            id=str(uuid.uuid4()),
            code=code,
            status="creada",
            event_type=payload.event_type,
            guests=payload.guests,
            budget_cop=payload.budget_cop,
            modality=payload.modality,
            total_cop=total_cop,
            customer_name=payload.customer.name,
            customer_email=payload.customer.email,
            customer_phone=payload.customer.phone,
            event_date=payload.event_date,
        )
        items = [
            ReservationItem(
                reservation_id=reservation.id,
                category=service.category,
                service_id=service.id,
                service_name=service.name,
                provider_name=service.provider_name,
                price_model=service.price_model,
                unit_price_cop=service.base_price_cop,
                cost_cop=costs[service.id],
            )
            for service in services
        ]
        try:
            save_reservation(session, reservation, items)
        except IntegrityError:
            if reservation_code_exists(session, code):
                continue
            raise
        return _response(reservation, payload.customer, payload.event_date, services, costs)

    raise AppError("INTERNAL_ERROR", "No fue posible completar la operación. Intente nuevamente.", 500)


def get_reservation_confirmation(code: str, session: Session) -> ReservationConfirmationResponse:
    reservation = get_reservation_by_code(session, code)
    if reservation is None:
        raise AppError("NOT_FOUND", "No encontramos una reserva con ese número.", 404)
    if reservation.status != "pagada":
        raise AppError("INVALID_STATE", "La reserva aún no está pagada.")

    payment = get_approved_payment(session, reservation.id)
    if payment is None:
        raise AppError("INVALID_STATE", "La reserva aún no está pagada.")

    items = get_reservation_items(session, reservation.id)
    return ReservationConfirmationResponse(
        code=reservation.code,
        status=reservation.status,
        modality=reservation.modality,
        total_cop=reservation.total_cop,
        items=[
            ReservationItemResponse(
                service_id=item.service_id,
                category=item.category,
                service_name=item.service_name,
                provider_name=item.provider_name,
                price_model=item.price_model,
                unit_price_cop=item.unit_price_cop,
                cost_cop=item.cost_cop,
            )
            for item in items
        ],
        customer=ReservationCustomerResponse(
            name=reservation.customer_name,
            email=reservation.customer_email,
            phone=reservation.customer_phone,
        ),
        event_date=reservation.event_date,
        payment=ReservationPaymentResponse(status=payment.status, reference=payment.reference),
    )
