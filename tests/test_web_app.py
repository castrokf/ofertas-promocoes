from app import app


def test_healthz():
    client = app.test_client()
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


def test_dashboard_uses_cached_data(monkeypatch):
    def fake_data(segment, limit, force_refresh=False):
        return {
            "segment": segment,
            "generated_at": 0,
            "deals": [],
            "stats": {"collected": 0, "approved": 0, "shown": 0, "rejected": 0},
            "errors": [],
        }

    monkeypatch.setattr("app.get_dashboard_data", fake_data)
    client = app.test_client()
    response = client.get("/?segment=games&limit=bad")

    assert response.status_code == 200
    assert b"AutoTechDealsX" in response.data
