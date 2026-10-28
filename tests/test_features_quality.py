import numpy as np
import pandas as pd
import pytest

from features import FEATURES, build_features, clean, standardize


MEDIANS = {
    "ambient_temp_c": 24.0,
    "humidity_pct": 55.0,
    "solar_irradiance_wm2": 100.0,
}


def row(**overrides):
    values = {
        "timestamp": "2024-01-01 12:00:00",
        "ambient_temp_c": 24.0,
        "humidity_pct": 55.0,
        "solar_irradiance_wm2": 100.0,
    }
    values.update(overrides)
    return pd.DataFrame([values])


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("temp", "ambient_temp_c"),
        ("temperature", "ambient_temp_c"),
        ("humidity", "humidity_pct"),
        ("solar", "solar_irradiance_wm2"),
        ("irradiance", "solar_irradiance_wm2"),
        ("time", "timestamp"),
        ("datetime", "timestamp"),
    ],
)
def test_standardize_aliases(alias, canonical):
    frame = row()
    frame = frame.rename(columns={canonical: alias})
    assert canonical in standardize(frame).columns


@pytest.mark.parametrize(
    ("column", "value", "expected"),
    [
        ("humidity_pct", -10, 0),
        ("humidity_pct", 120, 100),
        ("solar_irradiance_wm2", -50, 0),
        ("ambient_temp_c", -100, -60),
        ("ambient_temp_c", 100, 60),
    ],
)
def test_physical_bounds_are_clipped(column, value, expected):
    cleaned, report = clean(row(**{column: value}), MEDIANS)
    assert cleaned.iloc[0][column] == expected
    assert report["clipped"] == 1


@pytest.mark.parametrize(
    "bad_value",
    [None, "", "not-a-number", "nan", np.nan],
)
def test_missing_numeric_values_use_training_medians(bad_value):
    cleaned, report = clean(row(ambient_temp_c=bad_value), MEDIANS)
    assert cleaned.iloc[0]["ambient_temp_c"] == MEDIANS["ambient_temp_c"]
    assert report["missing_filled"] == 1


def test_invalid_timestamp_is_retained_and_warned():
    cleaned, report = clean(row(timestamp="not-a-date"), MEDIANS)
    assert len(cleaned) == 1
    assert report["bad_timestamps"] == 1
    assert report["warnings"]


def test_features_have_fixed_order_and_no_nan():
    cleaned, _ = clean(
        pd.DataFrame(
            [
                row().iloc[0].to_dict(),
                row(timestamp="2024-01-01 18:00:00").iloc[0].to_dict(),
            ]
        ),
        MEDIANS,
    )
    features = build_features(cleaned)
    assert list(features.columns) == FEATURES
    assert not features.isna().any().any()


@pytest.mark.parametrize(
    ("timestamp", "peak"),
    [
        ("2024-01-01 17:00:00", 0),
        ("2024-01-01 18:00:00", 1),
        ("2024-01-01 22:00:00", 1),
        ("2024-01-01 23:00:00", 0),
    ],
)
def test_peak_window_boundaries(timestamp, peak):
    cleaned, _ = clean(row(timestamp=timestamp), MEDIANS)
    assert int(build_features(cleaned).iloc[0]["is_peak_window"]) == peak


@pytest.mark.parametrize(
    ("temperature", "cdd", "hdd"),
    [(10, 0, 8), (18, 0, 0), (22, 0, 0), (30, 8, 0)],
)
def test_degree_day_features(temperature, cdd, hdd):
    cleaned, _ = clean(row(ambient_temp_c=temperature), MEDIANS)
    features = build_features(cleaned).iloc[0]
    assert features["cdd"] == cdd
    assert features["hdd"] == hdd


def test_cyclic_hour_features_repeat_after_24_hours():
    cleaned, _ = clean(
        pd.DataFrame(
            [
                row(timestamp="2024-01-01 03:00:00").iloc[0].to_dict(),
                row(timestamp="2024-01-02 03:00:00").iloc[0].to_dict(),
            ]
        ),
        MEDIANS,
    )
    features = build_features(cleaned)
    assert features.iloc[0]["hour_sin"] == pytest.approx(features.iloc[1]["hour_sin"])
    assert features.iloc[0]["hour_cos"] == pytest.approx(features.iloc[1]["hour_cos"])
