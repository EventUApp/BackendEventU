"""Rutas del módulo catalogo. Cada HU añade aquí sus endpoints (ver docs/ y CLAUDE.md)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.catalogo.service import get_home_data
from app.shared.db import get_session

router = APIRouter()


@router.get("/home")
def home(db: Annotated[Session, Depends(get_session)]) -> dict[str, Any]:
    return get_home_data(db)
