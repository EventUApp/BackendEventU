"""Dinero como entero en COP (ADR-04, RN-04, RN-15)."""


def cost_for_guests(price_model: str, base_price_cop: int, guests: int) -> int:
    """Costo de un servicio: fijo = precio base; por_invitado = precio x invitados, en COP enteros."""
    if price_model == "fijo":
        return base_price_cop
    if price_model == "por_invitado":
        return round(base_price_cop * guests)
    raise ValueError(f"Modelo de precio desconocido: {price_model}")
