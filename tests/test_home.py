from seed.load import load_seed


def test_home_returns_categories_and_featured_provider_summary(client, session):
    load_seed(session)

    r = client.get("/api/v1/home")

    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"categories", "featured"}
    assert len(body["categories"]) == 4
    assert [item["category"] for item in body["categories"]] == [
        "espacio",
        "alimentacion",
        "decoracion",
        "entretenimiento",
    ]
    assert all(item["count"] > 0 for item in body["categories"])
    assert len(body["featured"]) == 6
    first = body["featured"][0]
    assert first["featured"] is True
    assert first["cover_url"].startswith("https://")
    assert "price_from_cop" in first
    assert "rating_avg" in first
    assert "verification_status" in first


def test_home_featured_order_follows_rating_then_count(client, session):
    load_seed(session)

    r = client.get("/api/v1/home")
    featured = r.json()["featured"]

    assert len(featured) == 6
    for idx in range(1, len(featured)):
        prev = featured[idx - 1]
        curr = featured[idx]
        prev_sort = (prev["rating_avg"] or -1, prev["rating_count"], prev["id"])
        curr_sort = (curr["rating_avg"] or -1, curr["rating_count"], curr["id"])
        assert prev_sort >= curr_sort
