# features.py
# SINGLE SOURCE OF TRUTH: cleaning + features for training, predict.py, and backend
import json
import numpy as np
import pandas as pd

RAW = ["ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"]
CALENDAR = ["hour", "dow", "is_weekend", "hour_sin", "hour_cos", "is_peak_window"]
DERIVED = ["cdd", "hdd", "temp_x_hum"]
# month is NOT included because test contains month 7 (July) which is unseen in train
FEATURES = RAW + CALENDAR + DERIVED

ALIASES = {
    "temp": "ambient_temp_c", "temperature": "ambient_temp_c",
    "humidity": "humidity_pct", "solar": "solar_irradiance_wm2",
    "irradiance": "solar_irradiance_wm2", "time": "timestamp", "datetime": "timestamp",
}
CDD_BASE, HDD_BASE = 22.0, 18.0     # tuned from EDA


def load_medians(path="artifacts/medians.json"):
    with open(path) as f:
        return json.load(f)


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [ALIASES.get(c.strip().lower(), c.strip().lower()) for c in df.columns]
    return df


def clean(df: pd.DataFrame, medians: dict, interpolate: bool = False):
    """Never drops rows. Returns (df_with_ts_and_clean_numbers, report)."""
    df = standardize(df)
    missing_cols = [c for c in ["timestamp"] + RAW if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    report = {"rows": int(len(df)), "bad_timestamps": 0, "missing_filled": 0,
              "clipped": 0, "duplicates": 0, "warnings": []}

    df["ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
    report["bad_timestamps"] = int(df["ts"].isna().sum())
    report["duplicates"] = int(df["ts"].duplicated().sum())

    for c in RAW:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    report["missing_filled"] = int(df[RAW].isna().sum().sum())

    if interpolate and report["missing_filled"]:
        df[RAW] = df[RAW].interpolate(method="linear", limit_direction="both")
    for c in RAW:
        df[c] = df[c].fillna(medians[c])

    before = df[RAW].copy()
    df["humidity_pct"] = df["humidity_pct"].clip(0, 100)
    df["solar_irradiance_wm2"] = df["solar_irradiance_wm2"].clip(lower=0)
    df["ambient_temp_c"] = df["ambient_temp_c"].clip(-60, 60)
    report["clipped"] = int((before != df[RAW]).sum().sum())

    if report["bad_timestamps"]:
        report["warnings"].append(f"{report['bad_timestamps']} unreadable timestamp(s); default calendar values used.")
    return df, report


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """df must come out of clean(). Returns only FEATURES, in fixed order."""
    ts = df["ts"]
    hour = ts.dt.hour.fillna(12).astype(int)
    dow = ts.dt.dayofweek.fillna(0).astype(int)
    out = pd.DataFrame(index=df.index)
    for c in RAW:
        out[c] = df[c].astype(float)
    out["hour"] = hour
    out["dow"] = dow
    out["is_weekend"] = (dow >= 5).astype(int)
    out["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    out["is_peak_window"] = ((hour >= 18) & (hour <= 22)).astype(int)
    out["cdd"] = (df["ambient_temp_c"] - CDD_BASE).clip(lower=0)
    out["hdd"] = (HDD_BASE - df["ambient_temp_c"]).clip(lower=0)
    out["temp_x_hum"] = df["ambient_temp_c"] * df["humidity_pct"] / 100.0
    return out[FEATURES]