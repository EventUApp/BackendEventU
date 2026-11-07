import pytest

from app.recomendador.domain.recomendar import recomendar


@pytest.mark.xfail(raises=NotImplementedError, reason="HU_EU_01_03 implementa recomendar()", strict=True)
def test_recomendar_not_implemented_yet():
    recomendar(5_000_000, "boda", 50, [])
