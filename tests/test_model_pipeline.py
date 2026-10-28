import numpy as np
import pandas as pd

from features import build_features, clean
from ml_lab.model_selection import candidate_models, chronological_rmse, chronological_split


def test_chronological_split_is_order_independent():
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="h"),
            "value": range(10),
        }
    )
    fit, validation = chronological_split(frame.sample(frac=1, random_state=7))

    assert len(fit) == 8
    assert len(validation) == 2
    assert fit["timestamp"].max() < validation["timestamp"].min()
    assert set(fit["value"]).isdisjoint(validation["value"])


def test_chronological_split_preserves_all_rows():
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=20, freq="h"),
            "value": range(20),
        }
    )
    fit, validation = chronological_split(frame, validation_fraction=0.25)
    assert len(fit) + len(validation) == len(frame)
    assert set(fit["value"]) | set(validation["value"]) == set(frame["value"])


def test_chronological_split_rejects_bad_timestamp():
    frame = pd.DataFrame({"timestamp": ["bad", "2024-01-01"], "value": [1, 2]})
    import pytest

    with pytest.raises(ValueError, match="unreadable"):
        chronological_split(frame)


def test_chronological_split_rejects_invalid_fraction():
    frame = pd.DataFrame(
        {"timestamp": pd.date_range("2024-01-01", periods=2, freq="h"), "value": [1, 2]}
    )
    import pytest

    with pytest.raises(ValueError, match="between"):
        chronological_split(frame, validation_fraction=1)


def test_gradient_boosting_beats_existing_extra_trees_baseline():
    train = pd.read_csv("data/train_telemetry.csv")
    medians = {
        column: float(pd.to_numeric(train[column], errors="coerce").median())
        for column in ("ambient_temp_c", "humidity_pct", "solar_irradiance_wm2")
    }
    cleaned, _ = clean(train, medians, interpolate=False)
    features = build_features(cleaned)
    target = train["target_demand_kw"]
    models = candidate_models()

    baseline = chronological_rmse(models["extra_trees"], features, target)
    candidate = chronological_rmse(models["gradient_boosting"], features, target)

    assert np.isfinite(candidate).all()
    assert candidate.mean() < baseline.mean()
