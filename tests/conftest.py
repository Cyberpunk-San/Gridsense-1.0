import pytest

import app.app as app_module
from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def deterministic_predictions(monkeypatch):
    """Keep route tests independent of QuickML credentials and network access."""
    monkeypatch.setattr(
        app_module,
        "predict_rows",
        lambda feature_rows: [100.0 + float(row["hour"]) for row in feature_rows],
    )
