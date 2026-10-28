# tests/test_api.py
# API integration tests for the Flask backend
import io
import json
import pytest
from app.app import app, run_forecast
import app.app as app_module
import pandas as pd


def test_health_endpoint(client):
    """Health check endpoint should return ok"""
    rv = client.get('/api/health')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'ok'


def test_forecast_csv_upload(client):
    """Forecast endpoint should accept CSV upload"""
    csv_data = """timestamp,ambient_temp_c,humidity_pct,solar_irradiance_wm2
2024-01-01 12:00:00,25.0,60.0,500.0
2024-01-01 13:00:00,26.0,55.0,600.0
"""
    rv = client.post('/api/forecast', data={
        'file': (io.BytesIO(csv_data.encode()), 'test.csv')
    }, content_type='multipart/form-data')

    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data['rows']) == 2
    assert 'signals' in data
    assert 'summary' in data
    assert data['summary']['forecast_hours'] == 2


def test_forecast_json_input(client):
    """Forecast endpoint should accept JSON input"""
    rows = [
        {"timestamp": "2024-01-01 12:00:00", "ambient_temp_c": 25.0, "humidity_pct": 60.0, "solar_irradiance_wm2": 500.0},
        {"timestamp": "2024-01-01 13:00:00", "ambient_temp_c": 26.0, "humidity_pct": 55.0, "solar_irradiance_wm2": 600.0},
    ]
    rv = client.post('/api/forecast', json={'rows': rows})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data["rows"]) == 2
    assert all("predicted_kw" in row for row in data["rows"])


def test_forecast_too_many_rows(client):
    """Should reject more than MAX_ROWS"""
    rows = [{"timestamp": f"2024-01-01 {h:02d}:00:00", "ambient_temp_c": 25.0, "humidity_pct": 60.0, "solar_irradiance_wm2": 500.0}
            for h in range(501)]
    rv = client.post('/api/forecast', json={'rows': rows})
    assert rv.status_code == 400
    data = json.loads(rv.data)
    assert 'error' in data


def test_forecast_empty_input(client):
    """Should reject empty input"""
    rv = client.post('/api/forecast', json={'rows': []})
    assert rv.status_code == 400


def test_forecast_missing_rows_key_returns_bad_request(client):
    rv = client.post("/api/forecast", json={"data": []})
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_forecast_missing_required_column_returns_bad_request(client):
    rv = client.post(
        "/api/forecast",
        json={"rows": [{"timestamp": "2024-01-01 00:00:00"}]},
    )
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_run_not_found_returns_404(client):
    rv = client.get("/api/runs/does-not-exist")
    assert rv.status_code == 404
    assert rv.get_json()["error"] == "Run not found"


def test_logs_endpoint_has_stable_shape(client):
    rv = client.get("/api/logs")
    assert rv.status_code == 200
    assert isinstance(rv.get_json()["logs"], list)


def test_demo_endpoint(client):
    """Demo endpoint should return a forecast"""
    rv = client.get('/api/demo')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data['rows']) == 24
    assert data["summary"]["forecast_hours"] == 24


def test_typical_day_endpoint(client):
    """Typical day endpoint should return a forecast"""
    rv = client.get('/api/typical-day')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data['rows']) == 24


def test_run_forecast_pipeline():
    """Test the core run_forecast function with mocked predictions"""
    # Create test data
    raw = pd.DataFrame([{
        "timestamp": "2024-01-01 12:00:00",
        "ambient_temp_c": 25.0,
        "humidity_pct": 60.0,
        "solar_irradiance_wm2": 500.0,
    }])

    result = run_forecast(raw, "test")
    assert result["source"] == "test"
    assert result["rows"][0]["predicted_kw"] == 112.0
    assert result["rows"][0]["grid_kw"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
