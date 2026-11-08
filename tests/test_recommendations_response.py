from app.recomendador.domain.tipos import (
    PackageItem,
    PackageResult,
    Recommendation,
    ServiceOption,
    Unavailable,
)
from seed.load import load_seed


def test_post_recommendations_maps_domain_packages_and_unavailable(client, session, monkeypatch):
    load_seed(session)
    observed: dict[str, object] = {}

    def fake_recommend(
        budget_cop: int, event_type: str, guests: int, catalog: tuple[ServiceOption, ...]
    ) -> Recommendation:
        observed["inputs"] = (budget_cop, event_type, guests)
        observed["catalog"] = catalog
        services = {
            "espacio": ServiceOption(
                "service-space",
                "provider-space",
                "Salón Central",
                "verificado",
                "espacio",
                "ahorro",
                "Salón",
                "fijo",
                100_000,
                1,
                500,
                ("boda",),
            ),
            "alimentacion": ServiceOption(
                "service-food",
                "provider-food",
                "Catering Central",
                "en_revision",
                "alimentacion",
                "ahorro",
                "Menú",
                "fijo",
                200_000,
                1,
                500,
                ("boda",),
            ),
            "decoracion": ServiceOption(
                "service-decor",
                "provider-decor",
                "Decoraciones Central",
                "verificado",
                "decoracion",
                "equilibrado",
                "Decoración",
                "fijo",
                50_000,
                1,
                500,
                ("boda",),
            ),
            "entretenimiento": ServiceOption(
                "service-music",
                "provider-music",
                "Música Central",
                "en_revision",
                "entretenimiento",
                "premium",
                "DJ",
                "fijo",
                90_000,
                1,
                500,
                ("boda",),
            ),
        }

        def package(modality: str, include_entertainment: bool = False) -> PackageResult:
            categories = ["espacio", "alimentacion", "decoracion"]
            if include_entertainment:
                categories.append("entretenimiento")
            items = tuple(
                PackageItem(services[category], index * 10_000)
                for index, category in enumerate(categories, start=1)
            )
            total_cop = sum(item.cost_cop for item in items)
            return PackageResult(modality, items, total_cop, budget_cop - total_cop)

        assert catalog
        return Recommendation(
            packages=(
                package("ahorro"),
                package("equilibrado", include_entertainment=True),
                package("premium", include_entertainment=True),
            ),
            unavailable=(),
        )

    monkeypatch.setattr("app.recomendador.service.recomendar", fake_recommend)

    response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 2_500_000, "event_type": "boda", "guests": 70},
    )

    assert response.status_code == 200
    assert observed["inputs"] == (2_500_000, "boda", 70)
    catalog = observed["catalog"]
    assert isinstance(catalog, tuple)
    assert catalog
    assert all(service.event_types == ("boda",) for service in catalog)
    assert all(service.min_guests <= 70 <= service.max_guests for service in catalog)

    body = response.json()
    assert [package["modality"] for package in body["packages"]] == [
        "ahorro",
        "equilibrado",
        "premium",
    ]
    assert body["unavailable"] == []
    for package in body["packages"]:
        items = [item for category in package["breakdown"] for item in category["items"]]
        assert package["total_cop"] == sum(item["cost_cop"] for item in items)
        assert package["total_cop"] <= 2_500_000
        assert package["remaining_cop"] == 2_500_000 - package["total_cop"]
        assert {
            "espacio",
            "alimentacion",
            "decoracion",
        }.issubset({category["category"] for category in package["breakdown"]})
        for category in package["breakdown"]:
            assert category["subtotal_cop"] == sum(item["cost_cop"] for item in category["items"])
            assert isinstance(category["subtotal_cop"], int)
            assert all(isinstance(item["cost_cop"], int) for item in category["items"])

    first_package = body["packages"][0]
    assert [category["category"] for category in first_package["breakdown"]] == [
        "espacio",
        "alimentacion",
        "decoracion",
    ]
    first_item = first_package["breakdown"][0]["items"][0]
    assert first_item == {
        "service_id": "service-space",
        "name": "Salón",
        "provider_id": "provider-space",
        "provider_name": "Salón Central",
        "verification_status": "verificado",
        "cost_cop": 10_000,
    }

    package_with_optional_category = body["packages"][1]
    assert package_with_optional_category["breakdown"][-1]["category"] == "entretenimiento"

    repeated_response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 2_500_000, "event_type": "boda", "guests": 70},
    )
    assert repeated_response.status_code == 200
    assert repeated_response.json() == body

    monkeypatch.setattr(
        "app.recomendador.service.recomendar",
        lambda *_: Recommendation((), (Unavailable("premium", "sin_servicios"),)),
    )
    unavailable_response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 2_500_000, "event_type": "boda", "guests": 70},
    )
    assert unavailable_response.status_code == 200
    assert unavailable_response.json() == {
        "packages": [],
        "unavailable": [{"modality": "premium", "cause": "sin_servicios"}],
    }


def test_post_recommendations_returns_generic_error_when_recommender_fails(client, monkeypatch):
    def fail(*_args: object) -> Recommendation:
        raise RuntimeError("internal implementation detail")

    monkeypatch.setattr("app.recomendador.service.recomendar", fail)

    response = client.post(
        "/api/v1/recommendations",
        json={"budget_cop": 2_500_000, "event_type": "boda", "guests": 70},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "No fue posible completar la operación. Intente nuevamente.",
        }
    }
