"""Función pura del recomendador (SAD §6). La implementa HU_EU_01_03.

Invariante: el total de todo paquete devuelto es <= presupuesto (RN-01).
"""

from collections.abc import Sequence

from app.recomendador.domain.tipos import Recommendation, ServiceOption


def recomendar(
    presupuesto: int, tipo_evento: str, invitados: int, catalogo: Sequence[ServiceOption]
) -> Recommendation:
    raise NotImplementedError("HU_EU_01_03: ver docs/20261105_SAD_EU.md §6")
