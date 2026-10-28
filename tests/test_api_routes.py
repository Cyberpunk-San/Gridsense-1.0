import io
import os


def test_runs_endpoint_has_stable_shape(client):
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert isinstance(response.get_json()["runs"], list)


def test_predict_proxy_requires_authentication(client, monkeypatch):
    monkeypatch.setenv("PREDICT_PROXY_KEY", "secret")
    response = client.post(
        "/api/predict_csv",
        data={"file": (io.BytesIO(b"timestamp,ambient_temp_c\n"), "input.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 401


def test_predict_proxy_accepts_valid_key(client, monkeypatch):
    monkeypatch.setenv("PREDICT_PROXY_KEY", "secret")
    payload = (
        "timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2\n"
        "2024-01-01 00:00:00,25,50,0\n"
    )
    response = client.post(
        "/api/predict_csv",
        headers={"X-PREDICT-KEY": "secret"},
        data={"file": (io.BytesIO(payload.encode()), "input.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert len(response.get_json()["predictions"]) == 1


def test_predict_proxy_rejects_oversized_input(client, monkeypatch):
    monkeypatch.setenv("PREDICT_PROXY_KEY", "secret")
    rows = ["timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2"]
    rows.extend(f"2024-01-01 00:00:00,25,50,0" for _ in range(2001))
    response = client.post(
        "/api/predict_csv",
        headers={"X-PREDICT-KEY": "secret"},
        data={"file": (io.BytesIO(("\n".join(rows)).encode()), "input.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Too many rows" in response.get_json()["error"]
