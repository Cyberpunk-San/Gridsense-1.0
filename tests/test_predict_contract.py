import numpy as np
import pandas as pd
import pytest

import predict


def input_frame(count=3):
    return pd.DataFrame(
        [
            {
                "timestamp": f"2024-01-01 {hour:02d}:00:00",
                "ambient_temp_c": 24.0,
                "humidity_pct": 55.0,
                "solar_irradiance_wm2": 100.0,
            }
            for hour in range(count)
        ]
    )


def test_predict_preserves_row_count_and_returns_finite_values(monkeypatch):
    monkeypatch.setenv("PREDICTION_MODE", "local")
    predict._LOCAL_MODEL = None

    values = predict.predict(input_frame(5))

    assert isinstance(values, np.ndarray)
    assert values.shape == (5,)
    assert np.isfinite(values).all()


def test_predict_rejects_non_dataframe():
    with pytest.raises(TypeError, match="DataFrame"):
        predict.predict([{"timestamp": "2024-01-01 00:00:00"}])


def test_predict_rejects_unknown_mode(monkeypatch):
    monkeypatch.setenv("PREDICTION_MODE", "unknown")
    with pytest.raises(ValueError, match="PREDICTION_MODE"):
        predict.predict(input_frame(1))


def test_quickml_mode_requires_complete_credentials(monkeypatch):
    monkeypatch.setenv("PREDICTION_MODE", "quickml")
    for name in (
        "QUICKML_ENDPOINT_URL",
        "QUICKML_ENDPOINT_KEY",
        "QUICKML_ORG_ID",
        "ZOHO_CLIENT_ID",
        "ZOHO_CLIENT_SECRET",
        "ZOHO_REFRESH_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="requires complete QuickML"):
        predict.predict(input_frame(1))


def test_predict_rejects_wrong_prediction_length(monkeypatch):
    monkeypatch.setenv("PREDICTION_MODE", "local")
    monkeypatch.setattr(predict, "_local_model_predict", lambda features: np.array([1.0]))

    with pytest.raises(RuntimeError, match="Expected 2 predictions"):
        predict.predict(input_frame(2))


def test_predict_rejects_non_finite_prediction(monkeypatch):
    monkeypatch.setenv("PREDICTION_MODE", "local")
    monkeypatch.setattr(
        predict,
        "_local_model_predict",
        lambda features: np.array([np.nan]),
    )

    with pytest.raises(RuntimeError, match="non-finite"):
        predict.predict(input_frame(1))
