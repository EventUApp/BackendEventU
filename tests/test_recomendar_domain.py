from app.recomendador.domain.recomendar import recomendar
from app.recomendador.domain.tipos import ServiceOption


def service(
    service_id: str,
    category: str,
    price: int,
    *,
    price_model: str = "fijo",
    min_guests: int = 1,
    max_guests: int = 500,
    event_types: tuple[str, ...] = ("boda",),
) -> ServiceOption:
    return ServiceOption(
        id=service_id,
        provider_id=f"provider-{service_id}",
        provider_name="Proveedor",
        verification_status="en_revision",
        category=category,
        level="equilibrado",
        name=service_id,
        price_model=price_model,
        base_price_cop=price,
        min_guests=min_guests,
        max_guests=max_guests,
        event_types=event_types,
    )


def test_recomendar_genera_tres_modalidades_con_totales_y_saldos():
    catalog = (
        service("space", "espacio", 300_000),
        service("food", "alimentacion", 250_000),
        service("decor", "decoracion", 100_000),
        service("music", "entretenimiento", 50_000),
    )

    recommendation = recomendar(1_000_000, "boda", 80, catalog)

    assert [package.modality for package in recommendation.packages] == [
        "ahorro",
        "equilibrado",
        "premium",
    ]
    assert recommendation.unavailable == ()
    assert [{item.service.category for item in package.items} for package in recommendation.packages] == [
        {"espacio", "alimentacion", "decoracion"},
        {"espacio", "alimentacion", "decoracion", "entretenimiento"},
        {"espacio", "alimentacion", "decoracion", "entretenimiento"},
    ]
    for package in recommendation.packages:
        assert package.total_cop == sum(item.cost_cop for item in package.items)
        assert package.total_cop <= 1_000_000
        assert package.remaining_cop == 1_000_000 - package.total_cop
        assert {item.service.category for item in package.items} >= {
            "espacio",
            "alimentacion",
            "decoracion",
        }
    assert [item.service.category for item in recommendation.packages[0].items] == [
        "espacio",
        "alimentacion",
        "decoracion",
    ]


def test_recomendar_filtra_evento_capacidad_y_calcula_precio_por_invitado():
    catalog = (
        service("space", "espacio", 100_000, min_guests=10, max_guests=100),
        service("food", "alimentacion", 2_500, price_model="por_invitado"),
        service("decor", "decoracion", 20_000),
        service("wrong-event", "espacio", 1, event_types=("cumpleanos",)),
        service("too-small", "alimentacion", 1, max_guests=79),
        service("too-large", "decoracion", 1, min_guests=81),
    )

    recommendation = recomendar(1_000_000, "boda", 80, catalog)

    for package in recommendation.packages:
        costs = {item.service.category: item.cost_cop for item in package.items}
        assert costs == {
            "espacio": 100_000,
            "alimentacion": 200_000,
            "decoracion": 20_000,
        }
        assert all(item.service.id not in {"wrong-event", "too-small", "too-large"} for item in package.items)


def test_recomendar_aplica_desempate_por_identificador_y_seleccion_de_modalidad():
    catalog = (
        service("space-cheapest-z", "espacio", 100_000),
        service("space-cheapest-a", "espacio", 100_000),
        service("space-middle", "espacio", 200_000),
        service("space-premium-z", "espacio", 300_000),
        service("space-premium-a", "espacio", 300_000),
        service("food", "alimentacion", 100_000),
        service("decor", "decoracion", 50_000),
    )

    recommendation = recomendar(2_000_000, "boda", 80, catalog)

    by_modality = {
        package.modality: next(
            item.service.id for item in package.items if item.service.category == "espacio"
        )
        for package in recommendation.packages
    }
    assert by_modality == {
        "ahorro": "space-cheapest-a",
        "equilibrado": "space-middle",
        "premium": "space-premium-a",
    }


def test_recomendar_reparte_tope_si_entretenimiento_no_cabe():
    catalog = (
        service("space-low", "espacio", 320_000),
        service("space-middle", "espacio", 350_000),
        service("space-high", "espacio", 370_000),
        service("food", "alimentacion", 300_000),
        service("decor", "decoracion", 100_000),
        service("music", "entretenimiento", 90_000),
    )

    recommendation = recomendar(1_000_000, "boda", 80, catalog)

    balanced = next(package for package in recommendation.packages if package.modality == "equilibrado")
    selected_space = next(item.service.id for item in balanced.items if item.service.category == "espacio")
    assert selected_space == "space-middle"
    assert all(item.service.category != "entretenimiento" for item in balanced.items)


def test_recomendar_devuelve_solo_modalidades_que_caben_en_su_objetivo():
    catalog = (
        service("space", "espacio", 400_000),
        service("food", "alimentacion", 250_000),
        service("decor", "decoracion", 150_000),
    )

    recommendation = recomendar(1_000_000, "boda", 80, catalog)

    assert [package.modality for package in recommendation.packages] == ["equilibrado", "premium"]
    assert [(item.modality, item.cause) for item in recommendation.unavailable] == [
        ("ahorro", "presupuesto_insuficiente")
    ]
    assert all(package.total_cop <= 1_000_000 for package in recommendation.packages)


def test_recomendar_informa_rubro_obligatorio_sin_servicios_elegibles():
    catalog = (service("space", "espacio", 100_000), service("food", "alimentacion", 100_000))

    recommendation = recomendar(1_000_000, "boda", 80, catalog)

    assert recommendation.packages == ()
    assert [(item.modality, item.cause) for item in recommendation.unavailable] == [
        ("ahorro", "sin_servicios"),
        ("equilibrado", "sin_servicios"),
        ("premium", "sin_servicios"),
    ]
