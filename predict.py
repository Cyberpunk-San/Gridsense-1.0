#!/usr/bin/env python3
# predict.py — evaluator entry point (CLI)
# Rules it must never break: exactly one output row per input row, original timestamp string preserved, same order, always numeric.

import argparse
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from features import clean, build_features, load_medians
from quickml_client import predict_rows

ROOT = Path(__file__).resolve().parent
_LOCAL_MODEL = None


def _quickml_is_configured() -> bool:
    """Return true only when a complete published-endpoint configuration exists."""
    return all(os.getenv(name) for name in (
        "QUICKML_ENDPOINT_URL", "QUICKML_ENDPOINT_KEY", "QUICKML_ORG_ID",
        "ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN",
    ))


def _local_model_predict(features: pd.DataFrame) -> np.ndarray:
    """Offline development fallback trained only from the supplied training set.

    It makes the required ``predict(input_df)`` contract testable without
    publishing credentials.  A configured QuickML endpoint is always used for
    normal evaluation/deployment; this fallback is never represented as a
    QuickML result.
    """
    global _LOCAL_MODEL
    if _LOCAL_MODEL is None:
        try:
            from sklearn.ensemble import GradientBoostingRegressor
        except ImportError as exc:  # pragma: no cover - evaluation images include sklearn
            raise RuntimeError(
                "QuickML is not configured and scikit-learn is unavailable for the local fallback."
            ) from exc

        train_path = ROOT / "data" / "train_telemetry.csv"
        train = pd.read_csv(train_path)
        medians = {c: float(pd.to_numeric(train[c], errors="coerce").median())
                   for c in ("ambient_temp_c", "humidity_pct", "solar_irradiance_wm2")}
        train_clean, _ = clean(train, medians, interpolate=False)
        train_features = build_features(train_clean)
        _LOCAL_MODEL = GradientBoostingRegressor(
            n_estimators=400,
            learning_rate=0.03,
            max_depth=3,
            min_samples_leaf=3,
            random_state=42,
        ).fit(train_features, train["target_demand_kw"])
    return np.asarray(_LOCAL_MODEL.predict(features), dtype=float)


def predict(input_df: pd.DataFrame) -> np.ndarray:
    """Return one finite prediction for every input row, in the original order.

    This is the callable contract consumed by the supplied ``test_eval.py``.
    Set ``PREDICTION_MODE=quickml`` to require the published endpoint, or leave
    it unset during local development to use QuickML when configured and the
    reproducible offline model otherwise.
    """
    if not isinstance(input_df, pd.DataFrame):
        raise TypeError("predict(input_df) requires a pandas DataFrame")

    medians = load_medians(ROOT / "artifacts" / "medians.json")
    cleaned, _ = clean(input_df, medians, interpolate=False)
    features = build_features(cleaned)

    mode = os.getenv("PREDICTION_MODE", "auto").strip().lower()
    if mode not in {"auto", "quickml", "local"}:
        raise ValueError("PREDICTION_MODE must be one of: auto, quickml, local")
    if mode == "quickml" or (mode == "auto" and _quickml_is_configured()):
        if not _quickml_is_configured():
            raise RuntimeError("PREDICTION_MODE=quickml requires complete QuickML credentials.")
        values = np.asarray(predict_rows(features.to_dict(orient="records")), dtype=float)
    else:
        values = _local_model_predict(features)

    if len(values) != len(input_df):
        raise RuntimeError(f"Expected {len(input_df)} predictions, received {len(values)}.")
    if not np.isfinite(values).all():
        raise RuntimeError("Prediction source returned non-finite values.")
    return values


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    raw = pd.read_csv(a.input)
    ts_original = raw["timestamp"].astype(str).tolist() if "timestamp" in raw else [""] * len(raw)

    medians = load_medians(ROOT / "artifacts" / "medians.json")
    _, report = clean(raw, medians, interpolate=False)
    preds = predict(raw)

    # safety net: never output NaN/inf (keeps the file valid for the evaluator)
    bad = ~np.isfinite(preds)
    if bad.any():
        print(f"warning: {bad.sum()} non-finite predictions replaced", file=sys.stderr)
        fallback = float(np.nanmedian(preds[~bad])) if (~bad).any() else 130.0
        preds[bad] = fallback

    out = pd.DataFrame({"timestamp": ts_original, "target_demand_kw": np.round(preds, 4)})
    assert len(out) == len(raw)
    out.to_csv(a.output, index=False)
    print(f"wrote {len(out)} rows -> {a.output}  | cleaning report: {json.dumps(report)}")


if __name__ == "__main__":
    main()
