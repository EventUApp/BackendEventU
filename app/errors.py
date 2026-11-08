"""Formato de error uniforme {"error": {"code", "message", "fields"}} (SAD §7.2)."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("eventu")

GENERIC_MESSAGE = "No fue posible completar la operación. Intente nuevamente."
VALIDATION_MESSAGES = {
    "missing": "Este campo es obligatorio.",
    "int_parsing": "Ingrese un número entero.",
    "int_type": "Ingrese un número entero.",
    "greater_than_equal": "El valor está por debajo del mínimo permitido.",
    "less_than_equal": "El valor supera el máximo permitido.",
    "literal_error": "Seleccione una opción válida.",
}
GENERIC_VALIDATION_MESSAGE = "Revise el valor ingresado."
RESERVATION_VALIDATION_MESSAGES = {
    "customer.name": "Ingrese su nombre.",
    "customer.email": "Ingrese un correo electrónico válido.",
    "customer.phone": "Ingrese un teléfono de 10 dígitos.",
    "event_date": "Seleccione una fecha posterior a hoy.",
}


class AppError(Exception):
    """Error de negocio con código estable. La app móvil decide el texto que se muestra."""

    def __init__(self, code: str, message: str, status_code: int = 409, fields: dict[str, str] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields


def error_body(code: str, message: str, fields: dict[str, str] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return {"error": error}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message, exc.fields), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        for err in exc.errors():
            loc = [str(p) for p in err["loc"] if p not in ("body", "query", "path")]
            field = ".".join(loc) or "request"
            fields[field] = RESERVATION_VALIDATION_MESSAGES.get(
                field, VALIDATION_MESSAGES.get(str(err["type"]), GENERIC_VALIDATION_MESSAGE)
            )
        return JSONResponse(
            error_body("VALIDATION_ERROR", "Revise los datos ingresados.", fields), status_code=422
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "INTERNAL_ERROR"
        message = "No encontramos lo solicitado." if exc.status_code == 404 else GENERIC_MESSAGE
        return JSONResponse(error_body(code, message), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Se registra solo ruta y tipo: nunca cuerpos ni datos personales (RNF-SEG-02, RNF-SEG-05).
        logger.error("Error no controlado en %s %s: %s", request.method, request.url.path, type(exc).__name__)
        return JSONResponse(error_body("INTERNAL_ERROR", GENERIC_MESSAGE), status_code=500)
