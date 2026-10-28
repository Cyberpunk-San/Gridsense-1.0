import pandas as pd
import pytest

from app.ingest import MAX_ROWS, ingest_raw


def valid_rows(count=2):
    return pd.DataFrame(
        [
            {
                "timestamp": f"2024-01-01 {hour:02d}:00:00",
                "ambient_temp_c": 25,
                "humidity_pct": 50,
                "solar_irradiance_wm2": 100,
            }
            for hour in range(count)
        ]
    )


def test_ingest_sorts_rows_but_preserves_original_timestamp_values():
    raw = valid_rows()
    raw = raw.iloc[::-1].reset_index(drop=True)
    _, rows, quality = ingest_raw(raw)
    assert [item["hour"] for item in rows] == [0, 1]
    assert quality["rows"] == 2
    assert any("24 hourly" in warning for warning in quality["warnings"])


def test_ingest_warns_for_non_contiguous_hours():
    raw = valid_rows()
    raw.loc[1, "timestamp"] = "2024-01-01 03:00:00"
    _, _, quality = ingest_raw(raw)
    assert any("contiguous" in warning for warning in quality["warnings"])


def test_ingest_rejects_empty_frame():
    with pytest.raises(ValueError, match="no rows"):
        ingest_raw(pd.DataFrame())


def test_ingest_rejects_more_than_max_rows():
    with pytest.raises(ValueError, match=str(MAX_ROWS)):
        ingest_raw(valid_rows(MAX_ROWS + 1))


@pytest.mark.parametrize(
    "missing",
    ["timestamp", "ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"],
)
def test_ingest_rejects_missing_required_columns(missing):
    raw = valid_rows().drop(columns=missing)
    with pytest.raises(ValueError, match="Missing required columns"):
        ingest_raw(raw)


def test_ingest_interpolates_missing_weather_values():
    raw = valid_rows(3)
    raw.loc[1, "ambient_temp_c"] = None
    features, rows, quality = ingest_raw(raw)
    assert len(features) == 3
    assert rows[1]["ambient_temp_c"] == pytest.approx(25)
    assert quality["missing_filled"] == 1
