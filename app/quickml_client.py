# QuickML client for GridSense
import os
import time
import math
import requests

ACCOUNTS = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
_tok = {"value": None, "exp": 0}

FEATURE_COLUMNS = [
    "ambient_temp_c",
    "humidity_pct",
    "solar_irradiance_wm2",
    "hour",
    "dow",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "is_peak_window",
    "cdd",
    "hdd",
    "temp_x_hum",
]

TARGET_COLUMN = "target_demand_kw"


def _access_token():
    """Refresh Zoho OAuth token when needed."""
    if _tok["value"] and time.time() < _tok["exp"] - 300:
        return _tok["value"]

    r = requests.post(
        f"{ACCOUNTS}/oauth/v2/token",
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["ZOHO_CLIENT_ID"],
            "client_secret": os.environ["ZOHO_CLIENT_SECRET"],
            "refresh_token": os.environ["ZOHO_REFRESH_TOKEN"],
        },
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    _tok["value"] = j["access_token"]
    _tok["exp"] = time.time() + int(j.get("expires_in", 3600))
    return _tok["value"]


def _headers():
    return {
        "Authorization": f"Zoho-oauthtoken {_access_token()}",
        "X-QUICKML-ENDPOINT-KEY": os.environ["QUICKML_ENDPOINT_KEY"],
        "CATALYST-ORG": os.getenv("QUICKML_ORG_ID") or os.environ["X_ZOHO_CATALYST_ORG_ID"],
        "Environment": os.getenv("QUICKML_ENV", "Development"),
        "Content-Type": "application/json",
    }


def build_quickml_payload(row: dict) -> dict:
    """Build the exact feature payload expected by the model."""
    missing = [c for c in FEATURE_COLUMNS if c not in row]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    data = {}
    for col in FEATURE_COLUMNS:
        try:
            data[col] = float(row[col])
        except (TypeError, ValueError):
            raise ValueError(f"Feature '{col}' must be numeric, got: {row[col]!r}")

    return {"data": data}


def parse_quickml_prediction(payload: dict) -> float:
    """Handle the validated response shape: {'result': [value]}"""
    if not isinstance(payload, dict):
        raise ValueError("QuickML response must be a JSON object")

    result = payload.get("result")
    if not isinstance(result, list) or len(result) == 0:
        raise ValueError("QuickML response missing 'result' list")

    raw_value = result[0]
    try:
        prediction = float(raw_value)
    except (TypeError, ValueError):
        raise ValueError(f"Prediction is not numeric: {raw_value!r}")

    if not (0 < prediction < 10000):
        raise ValueError(f"Prediction out of expected range: {prediction}")

    return prediction


def _local_fallback_prediction(feature_rows: list[dict]) -> list[float]:
    """Deterministic fallback for local/offline use."""
    preds = []
    for row in feature_rows:
        hour = float(row.get("hour", 12))
        temp = float(row.get("ambient_temp_c", 25))
        solar = float(row.get("solar_irradiance_wm2", 0))

        base = 75.0
        if 18 <= hour <= 21:
            hour_factor = 95.0 * math.sin((hour - 17) / 4.0 * math.pi)
        elif 9 <= hour <= 15:
            hour_factor = 55.0 * math.sin((hour - 8) / 8.0 * math.pi)
        elif 0 <= hour <= 6:
            hour_factor = -20.0 + (hour * 2.0)
        else:
            hour_factor = 25.0

        temp_effect = max(0.0, temp - 22.0) * 3.5 + max(0.0, 16.0 - temp) * 2.0
        solar_damping = -min(25.0, solar * 0.03)
        kw = max(40.0, base + hour_factor + temp_effect + solar_damping)
        preds.append(round(float(kw), 2))

    return preds


def predict_rows(feature_rows: list[dict], batch=100, retries=3) -> list[float]:
    """Call the published QuickML endpoint and safely return predictions."""
    url = os.getenv("QUICKML_ENDPOINT_URL")
    if not url:
        return _local_fallback_prediction(feature_rows)

    out = []
    for i in range(0, len(feature_rows), batch):
        chunk = feature_rows[i:i + batch]
        for attempt in range(retries):
            try:
                r = requests.post(url, json={"data": chunk}, headers=_headers(), timeout=60)
                if r.status_code == 401:
                    _tok["value"] = None
                r.raise_for_status()
                payload = r.json()
                preds = payload.get("result") or payload.get("predictions") or payload.get("data") or []
                if not isinstance(preds, list) or len(preds) != len(chunk):
                    raise ValueError(f"Expected {len(chunk)} predictions, got {len(preds) if isinstance(preds, list) else 'non-list'}")
                out.extend([float(p) if not isinstance(p, dict) else float(p.get("target_demand_kw", p.get("value", 0))) for p in preds])
                break
            except Exception:
                if attempt == retries - 1:
                    return _local_fallback_prediction(feature_rows)
                time.sleep(1.5 * (attempt + 1))

    return out
