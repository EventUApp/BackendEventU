import pytest

from app.shared.money import cost_for_guests


def test_fixed_price():
    assert cost_for_guests("fijo", 450_000, 80) == 450_000


def test_per_guest_price_is_integer():
    assert cost_for_guests("por_invitado", 14_000, 30) == 420_000
    assert isinstance(cost_for_guests("por_invitado", 14_000, 30), int)


def test_unknown_model():
    with pytest.raises(ValueError):
        cost_for_guests("otro", 1, 1)
