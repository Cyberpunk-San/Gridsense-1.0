# app/ingest.py
# Data ingestion and validation
from pathlib import Path

import pandas as pd

try:  # Package import used by tests and WSGI servers.
    from .features import clean, build_features, load_medians
except ImportError:  # pragma: no cover - direct AppSail entry point
    from features import clean, build_features, load_medians


APP_DIR = Path(__file__).resolve().parent
MEDIANS = load_medians(APP_DIR / "artifacts" / "medians.json")
MAX_ROWS = 500


def ingest_raw(raw: pd.DataFrame, source: str = "csv_upload"):
    """
    Main ingestion pipeline: validate, clean, build features.
    Returns (feature_rows_for_quickml, cleaned_rows_with_original_ts, quality_report)
    """
    if len(raw) == 0:
        raise ValueError("The file has no rows.")
    if len(raw) > MAX_ROWS:
        raise ValueError(f"Too many rows ({len(raw)}). Max {MAX_ROWS}.")

    raw = raw.copy()

    # Parse timestamps for sorting, keep original strings for output
    raw["_ts_parsed"] = pd.to_datetime(raw.get("timestamp"), errors="coerce")
    raw = raw.sort_values("_ts_parsed", kind="stable").drop(columns="_ts_parsed").reset_index(drop=True)

    # Clean and validate
    df, quality = clean(raw, MEDIANS, interpolate=True)

    if len(raw) != 24:
        quality["warnings"].append(
            f"Expected 24 hourly rows for a full-day forecast; received {len(raw)}."
        )
    valid_timestamps = df["ts"].dropna().sort_values()
    if len(valid_timestamps) > 1 and (
        valid_timestamps.diff().dropna().dt.total_seconds().ne(3600).any()
    ):
        quality["warnings"].append("Forecast timestamps are not contiguous hourly readings.")

    # Build features for QuickML
    X = build_features(df)
    feature_rows = X.to_dict(orient="records")

    # Prepare cleaned rows with original timestamps for response
    cleaned_rows = []
    for i, (_, r) in enumerate(df.iterrows()):
        cleaned_rows.append({
            "timestamp": str(raw["timestamp"].iloc[i]),
            "hour": int(X["hour"].iloc[i]),
            "ambient_temp_c": float(r["ambient_temp_c"]),
            "humidity_pct": float(r["humidity_pct"]),
            "solar_irradiance_wm2": float(r["solar_irradiance_wm2"]),
            "_raw_kw": None,  # filled after prediction
        })

    return feature_rows, cleaned_rows, quality
