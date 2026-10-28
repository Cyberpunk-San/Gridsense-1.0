# HackSphere 3.0 — Smart Energy Microgrid & Demand Forecasting Engine
### Architecture and verification plan

> This is a reference implementation plan. Replace every example or placeholder metric with a measured result before submission.
> Rule of the whole plan: **correct output first, simple pipeline, easy to optimise later, small time and small space.**
> The dates below are planning examples; verify the actual submission deadline separately.

---

## Verified implementation state — 27 Oct 2026

This section is the source of truth for measured values in this workspace. It supersedes estimates, `TBD` cells, and illustrative response values elsewhere in this planning document.

| Item | Verified value | Evidence |
|---|---:|---|
| Training telemetry | 4,000 rows | `data/train_telemetry.csv` |
| Sample inference telemetry | 1,000 rows | `data/sample_test_input.csv` |
| Training period | 2014-12-31 23:00 to 2015-06-16 14:00 | Dataset inspection |
| Sample inference period | 2015-06-16 15:00 to 2015-07-28 06:00 | Dataset inspection |
| Feature vector | 12 features | `features.py` / `artifacts/feature_order.json` |
| Controller thresholds | Storage: demand > 160 kW or hour 18–22; overload: demand >= 200 kW | `app/controller.py` tests |
| Automated tests | 104 passed | `python -m pytest tests -q` |
| Evaluator contract | `SUCCESS` | `python test_eval.py` |

### Measured model-selection metrics

Metrics use five chronological `TimeSeriesSplit` folds on the training set. They
are local-selection metrics only; the published QuickML validation metrics are
recorded in the section below.

| Model | RMSE, mean ± std (kW) |
|---|---:|
| RidgeCV | 19.652 ± 1.062 |
| Extra Trees, 500 estimators, `min_samples_leaf=2` | 11.745 ± 2.501 |
| Gradient Boosting, 400 estimators, learning rate 0.03 | **10.650 ± 1.926** |
| LightGBM, 350 estimators | 12.672 ± 3.240 |

The Gradient Boosting candidate is now the local evaluator fallback. It was
selected using the same fixed feature contract and five chronological folds.
The earlier Extra Trees benchmark achieved **15.434 kW RMSE**, **11.868 kW MAE**, and
**0.936 R²** on a chronological 1,000-row holdout (first 3,000 rows train;
final 1,000 validate). These are local-selection metrics, not the official
QuickML hidden-test score.

### Published QuickML validation metrics

The published QuickML regression model reported these validation metrics:

| Metric | Score |
|---|---:|
| Mean Absolute Error (MAE) | **7.338** |
| Mean Squared Error (MSE) | **83.5484** |
| Root Mean Squared Error (RMSE) | **9.1405** |
| Root Mean Squared Log Error (RMSLE) | **0.0682** |
| R² Score | **0.9666** |
| Mean Absolute Percentage Error (MAPE) | **5.2217%** |

RMSE is the primary model-accuracy score for the 35% judging criterion. These
are QuickML validation metrics and should not be described as the hidden-test
score; the evaluator may use a separate hidden dataset.

### Display-metric rules now enforced

- Peak demand and chart axes are displayed in **kW**; forecast-horizon energy is displayed in **kWh** only after summing hourly readings.
- The dashboard no longer invents an “Actual Demand” series or diesel hours. It shows only API-derived forecast, grid, and renewable-storage values.
- Horizon counts, peak timestamp, total forecast energy, overload count, and grid-state percentages are derived from the current API response rather than fixed 24-hour/sample values.
- `predict.py` now exposes the callable `predict(input_df)` required by the supplied evaluator. In local development it uses a reproducible Extra Trees fallback only when QuickML is not configured; `PREDICTION_MODE=quickml` requires the published endpoint.

---

## 0. The winning idea in 10 lines

1. **70% of the marks are decided by two things**: the RMSE of the QuickML model (35%) and a live, working Catalyst URL (35%). Everything else is 30%. So we spend the first day on those two only.
2. The model sees only `timestamp + 3 weather columns`. So the accuracy comes from **good per-row features** (hour, weekday, cyclic time, temperature-based terms) and **picking the right QuickML algorithm** — not from fancy deep learning.
3. We make **one file `features.py` the single source of truth**. The same code prepares the training CSV, runs inside `predict.py`, and runs inside the backend. This kills the #1 bug in these hackathons: training features ≠ inference features.
4. We do **local experiments first** (LightGBM / Ridge on the laptop, 10 minutes) to learn which features matter, then **copy the winner into QuickML**. QuickML is the official model; the laptop is only our lab.
5. The transition controller is a **pure function with unit tests** (20% marks, easy to get 100%).
6. The live app is **one AppSail service** (Flask API + static dashboard). One URL, one deploy, fewer things to break.
7. The dashboard **opens already showing a forecast** (pre-loaded demo day) so the judge sees something in the first second, even if they never upload anything.
8. Every external call (QuickML, Data Store, Stratus) is wrapped so that **if it fails, the app still shows a clear message and never a blank page**.
9. We **deploy a skeleton early (Day 1 evening)** and only improve it after that. Never leave deployment for the last hour.
10. Final 6 hours before deadline = **freeze, test, README, submit**. No new features.

---

## 1. Where the marks come from

| Criteria | Weight | What decides it | Our move |
|---|---|---|---|
| Model accuracy (RMSE on hidden test, via `predict.py` → our QuickML endpoint) | 35% | Feature quality, algorithm, no train/inference mismatch, predict.py never crashing | EDA → local lab → QuickML → `test_eval.py` SUCCESS |
| Deployment & functionality (public Catalyst URL, end-to-end flow) | 35% | URL opens without login, upload → forecast → signals works | AppSail single service, demo day preloaded, health endpoint |
| Transition controller logic | 20% | Exact rules incl. boundaries (160, 200, hour 18–22 inclusive) | Pure function + boundary unit tests |
| UI / UX | 10% | Clean charts, state badges, alert banner | Chart.js dashboard, 5 clear blocks |

---

## 2. System architecture

```
                         ┌──────────────────────────────────────────────┐
   Judge / User  ───────▶│  Browser Dashboard (static HTML+JS+Chart.js) │
 (form / CSV upload)     └──────────────────────┬───────────────────────┘
                                                │ HTTPS (same origin)
                         ┌──────────────────────▼───────────────────────┐
                         │      Catalyst AppSail  (Python / Flask)       │
                         │                                               │
                         │  /api/forecast  ──► ingest.py   (clean)       │
                         │                 ──► features.py (features)    │
                         │                 ──► quickml_client.py ───────────┐
                         │                 ──► controller.py (rules)     │   │
                         │                 ──► battery.py   (SoC sim)    │   │
                         │                 ──► persist.py   (logs/runs)  │   │
                         └───────┬───────────────────────┬───────────────┘   │
                                 │                       │                   │
                    ┌────────────▼─────────┐  ┌──────────▼─────────┐  ┌──────▼───────────┐
                    │ Catalyst Stratus     │  │ Catalyst Data Store│  │ Catalyst QuickML │
                    │ (uploaded CSVs,      │  │ (run history,      │  │ published        │
                    │  result JSON)        │  │  system logs)      │  │ regression       │
                    └──────────────────────┘  └────────────────────┘  │ endpoint (REST)  │
                                                                      └──────▲───────────┘
   Evaluator machine:  python predict.py --input hidden.csv --output predictions.csv ─────┘
                       (same features.py, same QuickML endpoint)
```

**Why AppSail for everything (and not Slate + Functions + AppSail):** the problem statement lists Slate/Functions as a *recommendation*, and the deliverable says "Catalyst Slate / AppSail". One AppSail service that serves both the API and the static dashboard means one deploy, no CORS problems, no second URL to debug. If we have spare time on Day 2 evening, we can move the frontend to Slate (it is only copying the `static/` folder), but this is optional.

**Data flow for one forecast:**
1. User uploads CSV, fills the 24-row form, or clicks "Load demo day" / "Next 24h (typical weather)".
2. `ingest.py` validates + cleans (never drops a row), returns a data-quality report.
3. `features.py` builds the exact feature vector.
4. `quickml_client.py` sends rows to the QuickML endpoint, gets one number per row.
5. `controller.py` applies the grid rules → mode + overload flag + reason per hour.
6. `battery.py` simulates state of charge for the 24 hours.
7. Response JSON goes to the dashboard; run summary is saved to Data Store, raw CSV to Stratus (both optional, never blocking).

---

## 3. Repo layout

```
hacksphere-microgrid/
├── ARCHITECT.MD
├── README.md                    # setup, architecture, env vars (required deliverable)
├── predict.py                   # evaluator entry point (CLI)  ← 35% marks depend on this
├── test_eval.py                 # from starter kit, untouched
├── features.py                  # SINGLE SOURCE OF TRUTH: cleaning + features
├── artifacts/
│   ├── medians.json             # train medians for imputing (created by prepare_training.py)
│   └── feature_order.json
├── data/
│   ├── train_telemetry.csv      # from starter kit
│   ├── sample_test_input.csv    # from starter kit
│   └── demo_day.csv             # 24 rows picked for the preloaded demo
├── ml_lab/
│   ├── eda.py                   # Step 1
│   ├── prepare_training.py      # makes train_engineered.csv for QuickML upload
│   └── local_experiments.py     # Step 3 (laptop only, not deployed)
├── app/                         # ← this folder is the AppSail source directory
│   ├── app.py                   # Flask routes
│   ├── features.py              # copy of root features.py (sync with a script)
│   ├── ingest.py
│   ├── quickml_client.py
│   ├── controller.py
│   ├── battery.py
│   ├── persist.py
│   ├── config.py
│   ├── artifacts/               # medians.json etc.
│   ├── requirements.txt
│   ├── app-config.json         # created by catalyst CLI
│   └── static/
│       ├── index.html
│       ├── app.js
│       ├── style.css
│       └── vendor/chart.umd.min.js     # vendored, no CDN dependency
└── tests/
    ├── test_controller.py
    ├── test_features_parity.py
    └── test_api.py
```

Tip: keep **one** `features.py` in the repo root and let a tiny `sync.sh` copy it into `app/` before every deploy. Never edit the copy.

---

## 4. Step 1 — Understand the data first (30 minutes, do this tonight)

The most important unknown: **is the hidden test a random 20% or the last 20% in time?** The answer changes which features are safe.

`ml_lab/eda.py`
```python
import pandas as pd
RAW = ["ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"]
tr = pd.read_csv("data/train_telemetry.csv", parse_dates=["timestamp"])
te = pd.read_csv("data/sample_test_input.csv", parse_dates=["timestamp"])

print(tr.describe().T)
print("missing per col:\n", tr.isna().sum())
print("duplicate timestamps:", tr.timestamp.duplicated().sum())
print("train range:", tr.timestamp.min(), "→", tr.timestamp.max())
print("test  range:", te.timestamp.min(), "→", te.timestamp.max())

d = tr.timestamp.sort_values().diff().dropna()
print("share of 1-hour steps in train:", (d == pd.Timedelta("1h")).mean())
dt = te.timestamp.sort_values().diff().dropna()
print("share of 1-hour steps in test :", (dt == pd.Timedelta("1h")).mean())

print(tr.groupby(tr.timestamp.dt.hour).target_demand_kw.agg(["mean", "std"]).round(1))
print(tr.groupby(tr.timestamp.dt.dayofweek).target_demand_kw.mean().round(1))
print(tr.groupby(tr.timestamp.dt.month).target_demand_kw.mean().round(1))
print(tr[RAW + ["target_demand_kw"]].corr().round(2))
print("share >160:", (tr.target_demand_kw > 160).mean().round(3),
      " share >=200:", (tr.target_demand_kw >= 200).mean().round(3))
```

**Read the output like this (decision table):**

| What you see | What you do |
|---|---|
| Test dates are *inside* the train date range (random split) | Normal K-fold CV is fine. `month` and `dow` are safe. Rolling-weather features are **unsafe** (neighbouring rows are missing). |
| Test dates are *after* train max (chronological split) | Use time-based CV (train on early, validate on late). **Drop `month`** (unseen months break trees). Keep `hour`, `dow`, weather. |
| Test is contiguous hourly (≈100% 1-hour steps) | Optional: add rolling weather features (Section 5.3). |
| Demand clearly follows hour-of-day curve | Cyclic hour features + `is_peak_window` will carry most of the signal. |
| Demand rises with temperature above some point | Keep `cdd` (cooling degree). Tune its base temperature from the plot. |
| Missing values exist in train | Decide fill rule once, store in `medians.json`, reuse everywhere. |

---

## 5. Step 2 — `features.py` (the heart of consistency)

### 5.1 Cleaning rules (applied the same way in training, predict.py and the app)
- Column names: lowercase, trimmed, a few aliases accepted (`temp` → `ambient_temp_c`, etc.).
- `timestamp` parsed with `errors="coerce"`. A bad timestamp does **not** drop the row (predict.py must return one row per input). It gets default calendar values and a warning.
- Weather columns forced to numbers (`errors="coerce"`).
- Missing weather: in the **dashboard** path use time-ordered linear interpolation first, then median fill. In **predict.py** use median fill only (row-independent and deterministic).
- Physical clipping: humidity into 0–100, irradiance ≥ 0, temperature into −60…60 °C. Count how many values were clipped and show it in the data-quality report.

### 5.2 Per-row features (safe under both random and chronological split)

```python
# features.py
import json
import numpy as np
import pandas as pd

RAW = ["ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"]
CALENDAR = ["hour", "dow", "is_weekend", "hour_sin", "hour_cos", "is_peak_window"]
DERIVED = ["cdd", "hdd", "temp_x_hum"]
# add "month" ONLY if EDA says the test months appear in train
FEATURES = RAW + CALENDAR + DERIVED

ALIASES = {
    "temp": "ambient_temp_c", "temperature": "ambient_temp_c",
    "humidity": "humidity_pct", "solar": "solar_irradiance_wm2",
    "irradiance": "solar_irradiance_wm2", "time": "timestamp", "datetime": "timestamp",
}
CDD_BASE, HDD_BASE = 22.0, 18.0     # tune after EDA


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
        df[RAW] = df[RAW].interpolate(method="linear", limit_direction="both")  # df must be time-sorted
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
```

### 5.3 Optional upgrade (only if the decision table allows it)
Rolling weather means (3 h and 6 h of temperature) can help because buildings react slowly to heat. Rules so that it stays safe:
- Compute from **input weather columns only** (never from `target_demand_kw`, which is missing at test time).
- Sort by timestamp inside the function, compute `rolling("3h", on="ts", min_periods=1)`, then restore the original row order.
- Add it **only if** local CV improves RMSE by a clear margin (say > 3%) **and** the test file is contiguous hourly.
- Apply the identical function when preparing training data. If you are not sure, skip it. A simple model that never mismatches beats a smart one that does.

### 5.4 Create the training file for QuickML

`ml_lab/prepare_training.py`
```python
import json, os, pandas as pd
from features import clean, build_features, FEATURES, RAW

tr = pd.read_csv("data/train_telemetry.csv")
medians = {c: float(pd.to_numeric(tr[c], errors="coerce").median()) for c in RAW}
os.makedirs("artifacts", exist_ok=True)
json.dump(medians, open("artifacts/medians.json", "w"), indent=2)
json.dump(FEATURES, open("artifacts/feature_order.json", "w"))

tr = tr.dropna(subset=["target_demand_kw"]).drop_duplicates()
df, rep = clean(tr, medians, interpolate=False)
X = build_features(df)
X["target_demand_kw"] = df["target_demand_kw"].values
X.to_csv("train_engineered.csv", index=False)      # ← upload THIS to QuickML
print(rep, X.shape)
```
Note: the training target column is `target_demand_kw`, and `timestamp` is **not** in the upload (the model should not memorise dates).

---

## 6. Step 3 — Local lab (laptop only, 20–30 minutes)

Purpose: find out *which features and which model family win*, so the QuickML work becomes a copy job, not guesswork.

`ml_lab/local_experiments.py`
```python
import numpy as np, pandas as pd
from sklearn.model_selection import KFold, TimeSeriesSplit, cross_val_score
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
import lightgbm as lgb          # pip install lightgbm

df = pd.read_csv("train_engineered.csv")
y = df.pop("target_demand_kw"); X = df

# pick ONE, from the EDA decision table
cv = KFold(5, shuffle=True, random_state=42)      # random split
# cv = TimeSeriesSplit(5)                          # chronological split (keep original time order!)

models = {
    "ridge": RidgeCV(alphas=[0.1, 1, 10]),
    "rf":    RandomForestRegressor(300, min_samples_leaf=3, n_jobs=-1, random_state=0),
    "lgbm":  lgb.LGBMRegressor(n_estimators=600, learning_rate=0.03, num_leaves=31,
                               subsample=0.8, colsample_bytree=0.8, random_state=0, verbose=-1),
}
for name, m in models.items():
    rmse = -cross_val_score(m, X, y, cv=cv, scoring="neg_root_mean_squared_error")
    print(f"{name:6s}  RMSE {rmse.mean():.3f} ± {rmse.std():.3f}")
```
What to do with the result:
- If **ridge is close to lgbm** → the data is smooth/synthetic; choose the simple model in QuickML (less overfit risk).
- If **lgbm/rf clearly win** → choose a gradient-boosting / random-forest style algorithm in QuickML.
- Drop a feature, re-run, see if RMSE gets worse. Keep only features that help. This is the "iterate" loop, and each loop takes under a minute.
- Write the best local RMSE in your notes. It is the **target** QuickML must get close to.

---

## 7. Step 4 — Train and publish in QuickML (this is the critical path)

1. Create the Catalyst project (choose the data centre closest to you, e.g. India `.in`; **use the same region for OAuth later**).
2. QuickML → create pipeline → data source **Local File System** → upload `train_engineered.csv`.
3. Set **target = `target_demand_kw`**, task = regression. Hold out a validation split inside the pipeline so QuickML shows an RMSE.
4. Run two pipelines and compare RMSE:
   - **AutoML pipeline** first (fastest way to get a published endpoint tonight).
   - **Manual ML pipeline** with the algorithm family the local lab preferred (gradient boosting / random forest from *Regression Algorithms* or *Ensembling*), then a small hyper-parameter pass (depth, number of trees, learning rate).
5. Keep a tiny results table in the README:

   | Pipeline | Algorithm | Val RMSE | Version |
   |---|---|---|---|
   | local benchmark | Extra Trees | 11.781 ± 2.526 kW (chronological CV) | local only |
   | QuickML endpoint | RMSE 9.1405 kW; R² 0.9666 | validated | QuickML validation metrics supplied for the published model |

6. **Publish the best version as an endpoint.** Use the endpoint page's **Test the Model** box with one row from `sample_test_input.csv` (after feature building) to see the exact request and response JSON shape. Copy it. You need that shape for the next section.
7. Note down: endpoint URL, endpoint key, org id, environment (Development/Production).

> **Goal for tonight: a published endpoint that returns numbers, even if RMSE is not perfect.** Improving RMSE later is easy. Not having an endpoint on Day 2 is fatal.

**Careful:** every time the pipeline configuration changes, QuickML creates a new model version. After the final version is published, do not touch it unless you re-run `test_eval.py` again.

---

## 8. Step 5 — QuickML authentication and `predict.py`

QuickML endpoints are called with a POST and these headers (from the Catalyst docs for QuickML Pipeline Endpoints): `X-QUICKML-ENDPOINT-KEY`, `Authorization: Zoho-oauthtoken <access-token>`, `CATALYST-ORG`, and `Environment`. The token scope is `QuickML.deployment.READ`.

### 8.1 One-time OAuth setup (10 minutes)
1. Open the Zoho API console for your region (e.g. `api-console.zoho.in`) → **Self Client**.
2. Generate a grant code with scope `QuickML.deployment.READ` (the code expires in a few minutes, so do the next step immediately).
3. Exchange it for a **refresh token**:
   `POST https://accounts.zoho.in/oauth/v2/token` with `grant_type=authorization_code`, `client_id`, `client_secret`, `code`.
4. Store `CLIENT_ID`, `CLIENT_SECRET`, `REFRESH_TOKEN` as **environment variables only** (never in the repo).
5. At runtime, get a fresh access token (valid ~1 hour) with `grant_type=refresh_token`, cache it in memory, and refresh 5 minutes before expiry.

### 8.2 Shared client (used by both predict.py and the backend)

`quickml_client.py`
```python
import os, time, requests

ACCOUNTS = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
_tok = {"value": None, "exp": 0}


def _access_token():
    if _tok["value"] and time.time() < _tok["exp"] - 300:
        return _tok["value"]
    r = requests.post(f"{ACCOUNTS}/oauth/v2/token", data={
        "grant_type": "refresh_token",
        "client_id": os.environ["ZOHO_CLIENT_ID"],
        "client_secret": os.environ["ZOHO_CLIENT_SECRET"],
        "refresh_token": os.environ["ZOHO_REFRESH_TOKEN"],
    }, timeout=20)
    r.raise_for_status()
    j = r.json()
    _tok.update(value=j["access_token"], exp=time.time() + int(j.get("expires_in", 3600)))
    return _tok["value"]


def _headers():
    return {
        "Authorization": f"Zoho-oauthtoken {_access_token()}",
        "X-QUICKML-ENDPOINT-KEY": os.environ["QUICKML_ENDPOINT_KEY"],
        "CATALYST-ORG": os.environ["CATALYST_ORG_ID"],
        "Environment": os.getenv("CATALYST_ENV", "Development"),
        "Content-Type": "application/json",
    }


# ---- the ONLY two functions that depend on QuickML's JSON shape ----
def to_payload(feature_rows: list[dict]) -> dict:
    # VERIFY against the endpoint page → "Test the Model". Adjust key names if needed.
    return {"data": feature_rows}


def parse_response(j) -> list[float]:
    # VERIFY against the real response. Return one float per input row, same order.
    preds = j.get("predictions") or j.get("data") or j.get("result") or j
    return [float(p["target_demand_kw"] if isinstance(p, dict) else p) for p in preds]
# --------------------------------------------------------------------


def predict_rows(feature_rows: list[dict], batch=100, retries=3) -> list[float]:
    url = os.environ["QUICKML_ENDPOINT_URL"]
    out = []
    for i in range(0, len(feature_rows), batch):
        chunk = feature_rows[i:i + batch]
        for attempt in range(retries):
            try:
                r = requests.post(url, json=to_payload(chunk), headers=_headers(), timeout=60)
                if r.status_code == 401:            # token expired → force refresh once
                    _tok["value"] = None
                r.raise_for_status()
                preds = parse_response(r.json())
                if len(preds) != len(chunk):
                    raise ValueError(f"expected {len(chunk)} predictions, got {len(preds)}")
                out.extend(preds)
                break
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(1.5 * (attempt + 1))
    return out
```

### 8.3 `predict.py` (the evaluator runs this on a hidden file)

Rules it must never break: **exactly one output row per input row, original timestamp string preserved, same order, always numeric.**

```python
#!/usr/bin/env python3
import argparse, json, sys
import numpy as np, pandas as pd
from features import clean, build_features, load_medians
from quickml_client import predict_rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    raw = pd.read_csv(a.input)
    ts_original = raw["timestamp"].astype(str).tolist() if "timestamp" in raw else [""] * len(raw)

    medians = load_medians("artifacts/medians.json")
    df, report = clean(raw, medians, interpolate=False)
    X = build_features(df)

    preds = np.array(predict_rows(X.to_dict(orient="records")), dtype=float)

    # safety net: never output NaN/inf (keeps the file valid for the evaluator)
    bad = ~np.isfinite(preds)
    if bad.any():
        print(f"warning: {bad.sum()} non-finite predictions replaced", file=sys.stderr)
        fallback = float(np.nanmedian(preds[~bad])) if (~bad).any() else 130.0
        preds[bad] = fallback

    out = pd.DataFrame({"timestamp": ts_original, "target_demand_kw": np.round(preds, 4)})
    assert len(out) == len(raw)
    out.to_csv(a.output, index=False)
    print(f"wrote {len(out)} rows → {a.output}  | cleaning report: {json.dumps(report)}")

if __name__ == "__main__":
    main()
```
Notes:
- `predict.py` and `features.py` and `artifacts/medians.json` and `quickml_client.py` must sit in the same folder in the submission zip, so it runs from a clean clone.
- **Credentials question (ask the organisers today):** the evaluator will run `predict.py` on their side, but the statement also says "keep QuickML credentials secure". Ask on the hackathon channel how they expect credentials to be provided. Safe default plan:
  1. `predict.py` reads credentials from environment variables (documented in README).
  2. As a backup, expose a small `/api/predict_csv` route on our own AppSail app that holds the credentials server-side and returns predictions, and let `predict.py` use it when `QUICKML_ENDPOINT_URL` is not set (`PREDICT_PROXY_URL` env var). Protect it with a simple shared key and a row limit (≤ 2000 rows per call).
  Whatever they answer, mention the exact run instructions at the top of the README.
- Run `python predict.py --input data/sample_test_input.csv --output predictions.csv` and then `python test_eval.py`. Only `SUCCESS` counts.

---

## 9. Step 6 — Backend (Flask on AppSail)

### 9.1 API

| Method + path | What it does |
|---|---|
| `GET /api/health` | `{status, quickml_reachable, version}` — used by us and by judges to check the app is alive |
| `POST /api/forecast` | Accepts CSV file (multipart `file`) **or** JSON `{rows:[...]}`. Returns full forecast package (below) |
| `GET /api/demo` | Runs the forecast for `data/demo_day.csv` (used when the page first loads) |
| `GET /api/typical-day?date=YYYY-MM-DD` | Builds a 24-row weather day from the average hourly profile in train data (clearly labelled "estimated typical weather") |
| `GET /api/runs` / `GET /api/runs/<id>` | History from Data Store (optional) |
| `POST /api/predict_csv` | Backup proxy for `predict.py` (Section 8.3) |

### 9.2 Forecast response (the contract between backend and dashboard)

```json
{
  "run_id": "2026-10-27T10:15:00Z-ab12",
  "source": "csv_upload",
  "quality": {"rows": 24, "bad_timestamps": 0, "missing_filled": 2, "clipped": 0, "duplicates": 0, "warnings": []},
  "rows": [
    {
      "timestamp": "2024-01-01 18:00:00",
      "hour": 18,
      "ambient_temp_c": 23.1, "humidity_pct": 61.0, "solar_irradiance_wm2": 0.0,
      "predicted_kw": 148.72,
      "mode": "RENEWABLE_STORAGE",
      "reason": "Evening window 18:00–22:00",
      "overload": false,
      "soc_pct": 74.3,
      "battery_kw": -148.7
    }
  ],
  "signals": [
    {"timestamp": "2024-01-01 18:00:00", "command": "SWITCH_TO_BATTERY", "detail": "Evening window starts"},
    {"timestamp": "2024-01-01 23:00:00", "command": "SWITCH_TO_GRID", "detail": "Demand ≤ 160 kW and outside window"}
  ],
  "summary": {"peak_kw": 171.2, "peak_hour": "…", "renewable_hours": 7, "grid_hours": 17,
              "overload_hours": 0, "min_soc_pct": 41.0}
}
```

### 9.3 Ingestion rules (Requirement 2: "clean and validate")
- Accept CSV with or without `target_demand_kw` (ignore it if present).
- Sort by timestamp, keep original order index to return results in a sensible order.
- Row count: forecast **all** rows given. If the count is not 24, show a soft warning ("expected 24 hourly rows, got N") but still work. The dashboard shows the first 24 by default and a selector for the next 24-hour blocks if more are uploaded.
- Max 500 rows per request (protects the app).
- Gaps in time (missing hours) → warning, not an error.
- All problems come back in `quality.warnings` so the UI can show a friendly "Data check" card (this looks good for judges and costs almost nothing).

### 9.4 Flask skeleton

`app/app.py`
```python
import os, uuid, datetime as dt
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from features import clean, build_features, load_medians
from quickml_client import predict_rows
from controller import decide_all
from battery import simulate
import persist

app = Flask(__name__, static_folder="static", static_url_path="")
MEDIANS = load_medians("artifacts/medians.json")
MAX_ROWS = 500


@app.get("/")
def home():
    return send_from_directory("static", "index.html")


@app.get("/api/health")
def health():
    return jsonify(status="ok", version="1.0")


def run_forecast(raw: pd.DataFrame, source: str):
    if len(raw) == 0:
        raise ValueError("The file has no rows.")
    if len(raw) > MAX_ROWS:
        raise ValueError(f"Too many rows ({len(raw)}). Max {MAX_ROWS}.")
    raw = raw.copy()
    raw["_ts"] = pd.to_datetime(raw.get("timestamp"), errors="coerce")
    raw = raw.sort_values("_ts", kind="stable").drop(columns="_ts").reset_index(drop=True)

    df, quality = clean(raw, MEDIANS, interpolate=True)
    X = build_features(df)
    preds = predict_rows(X.to_dict(orient="records"))

    rows = []
    for i, p in enumerate(preds):
        r = df.iloc[i]
        rows.append({
            "timestamp": str(raw["timestamp"].iloc[i]),
            "hour": int(X["hour"].iloc[i]),
            "ambient_temp_c": float(r["ambient_temp_c"]),
            "humidity_pct": float(r["humidity_pct"]),
            "solar_irradiance_wm2": float(r["solar_irradiance_wm2"]),
            "predicted_kw": round(float(p), 2),
            "_raw_kw": float(p),            # controller uses the unrounded value
        })
    rows, signals = decide_all(rows)
    rows = simulate(rows)
    for r in rows:
        r.pop("_raw_kw", None)

    summary = {
        "peak_kw": max(r["predicted_kw"] for r in rows),
        "renewable_hours": sum(r["mode"] == "RENEWABLE_STORAGE" for r in rows),
        "grid_hours": sum(r["mode"] == "MAIN_GRID" for r in rows),
        "overload_hours": sum(r["overload"] for r in rows),
        "min_soc_pct": min(r["soc_pct"] for r in rows),
    }
    result = {"run_id": f"{dt.datetime.utcnow():%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:4]}",
              "source": source, "quality": quality, "rows": rows,
              "signals": signals, "summary": summary}
    persist.save_run_safely(result)           # never raises
    return result


@app.post("/api/forecast")
def forecast():
    try:
        if "file" in request.files:
            raw = pd.read_csv(request.files["file"])
            src = "csv_upload"
        else:
            raw = pd.DataFrame(request.get_json(force=True)["rows"])
            src = "manual_form"
        return jsonify(run_forecast(raw, src))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except Exception as e:                       # QuickML down, etc.
        app.logger.exception("forecast failed")
        return jsonify(error="Forecast service is temporarily unavailable.", detail=str(e)[:200]), 502


@app.get("/api/demo")
def demo():
    return jsonify(run_forecast(pd.read_csv("data/demo_day.csv"), "demo_day"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", 9000)))
```
Notes:
- AppSail gives the listening port through `X_ZOHO_CATALYST_LISTEN_PORT`. Use it.
- AppSail restricts writing files in the app directory while running → write temp files only to `/tmp`.
- `demo` route result can be **cached in memory** for 10 minutes so the first page load is instant.
- **Demo fallback (honest and visible):** if QuickML is unreachable during a live demo, the dashboard shows the last saved successful run with a clear badge "showing last saved forecast". Do not silently fake predictions.

---

## 10. Step 7 — Transition controller (20% marks, must be perfect)

Rules from the problem statement, per forecast hour, using the **predicted demand** and the **timestamp hour**:

| Condition | Result |
|---|---|
| demand **> 160** kW **OR** hour between **18 and 22 inclusive** | `RENEWABLE_STORAGE` |
| otherwise (demand **≤ 160** AND outside 18–22) | `MAIN_GRID` |
| demand **≥ 200** kW | **Critical Overload Alert** (independent of mode) |

Our reading of the boundaries (write this in the README so judges see we thought about it):
- Hour window is `18 <= hour <= 22` on the hourly row. So the 22:00 row is in the window, the 23:00 row is not.
- Exactly 160.00 kW outside the window → `MAIN_GRID` (rule says strictly greater than 160 for storage).
- Exactly 200.00 kW → overload (rule says ≥).
- The decision uses the **unrounded** prediction, the UI shows two decimals.

`app/controller.py`
```python
PEAK_START, PEAK_END = 18, 22
STORAGE_THRESHOLD_KW = 160.0
OVERLOAD_KW = 200.0


def decide(pred_kw: float, hour: int):
    in_window = PEAK_START <= hour <= PEAK_END
    over_threshold = pred_kw > STORAGE_THRESHOLD_KW
    if over_threshold and in_window:
        mode, reason = "RENEWABLE_STORAGE", "Demand > 160 kW and evening window 18:00–22:00"
    elif over_threshold:
        mode, reason = "RENEWABLE_STORAGE", "Demand > 160 kW"
    elif in_window:
        mode, reason = "RENEWABLE_STORAGE", "Evening window 18:00–22:00"
    else:
        mode, reason = "MAIN_GRID", "Demand ≤ 160 kW and outside 18:00–22:00"
    overload = pred_kw >= OVERLOAD_KW
    return mode, reason, overload


def decide_all(rows):
    """rows must each have _raw_kw and hour. Adds mode/reason/overload; builds control signals."""
    signals, prev_mode = [], None
    for r in rows:
        mode, reason, overload = decide(r["_raw_kw"], r["hour"])
        r.update(mode=mode, reason=reason, overload=overload)
        if mode != prev_mode:
            cmd = "SWITCH_TO_BATTERY" if mode == "RENEWABLE_STORAGE" else "SWITCH_TO_GRID"
            if prev_mode is None:
                cmd = "START_ON_BATTERY" if mode == "RENEWABLE_STORAGE" else "START_ON_GRID"
            signals.append({"timestamp": r["timestamp"], "command": cmd, "detail": reason})
            prev_mode = mode
        if overload:
            signals.append({"timestamp": r["timestamp"], "command": "CRITICAL_OVERLOAD_ALERT",
                            "detail": f"Predicted {r['predicted_kw']:.1f} kW ≥ 200 kW"})
    return rows, signals
```

`tests/test_controller.py`
```python
import pytest
from controller import decide

@pytest.mark.parametrize("kw,hour,mode,overload", [
    (100, 12, "MAIN_GRID", False),
    (160.0, 12, "MAIN_GRID", False),            # exactly 160 → grid
    (160.01, 12, "RENEWABLE_STORAGE", False),
    (100, 17, "MAIN_GRID", False),
    (100, 18, "RENEWABLE_STORAGE", False),      # window start inclusive
    (100, 22, "RENEWABLE_STORAGE", False),      # window end inclusive
    (100, 23, "MAIN_GRID", False),
    (199.99, 3, "RENEWABLE_STORAGE", False),
    (200.0, 3, "RENEWABLE_STORAGE", True),      # exactly 200 → overload
    (250, 20, "RENEWABLE_STORAGE", True),
    (120, 0, "MAIN_GRID", False),
])
def test_rules(kw, hour, mode, overload):
    m, _, o = decide(kw, hour)
    assert (m, o) == (mode, overload)
```

---

## 11. Step 8 — Battery state-of-charge (the dashboard needs it)

The statement asks for "battery state-of-charge" on the dashboard but gives **no battery data**. So this is a clearly-labelled **simulation with configurable assumptions**. Keep it simple and explain it on screen ("Battery model assumptions" tooltip).

`app/battery.py`
```python
from dataclasses import dataclass

@dataclass
class BatteryCfg:
    capacity_kwh: float = 1200.0     # tune after EDA so a typical evening does not hit the floor
    soc0_pct: float = 80.0           # starting state of charge
    min_soc_pct: float = 10.0
    max_discharge_kw: float = 250.0
    max_charge_kw: float = 80.0
    efficiency: float = 0.95
    pv_kwp: float = 120.0            # simulated solar array that charges the battery

def simulate(rows, cfg: BatteryCfg = BatteryCfg()):
    soc = cfg.capacity_kwh * cfg.soc0_pct / 100
    floor = cfg.capacity_kwh * cfg.min_soc_pct / 100
    for r in rows:
        pv_kw = cfg.pv_kwp * r["solar_irradiance_wm2"] / 1000.0
        charge_kw = min(pv_kw * cfg.efficiency, cfg.max_charge_kw)
        discharge_kw = 0.0
        if r["mode"] == "RENEWABLE_STORAGE":
            discharge_kw = min(r["_raw_kw"], cfg.max_discharge_kw, max(soc - floor, 0.0))  # 1-hour step: kW≈kWh
        soc = min(max(soc + charge_kw - discharge_kw, floor if discharge_kw else 0), cfg.capacity_kwh)
        r["soc_pct"] = round(100 * soc / cfg.capacity_kwh, 1)
        r["battery_kw"] = round(charge_kw - discharge_kw, 1)      # + charging, − discharging
        r["battery_low"] = r["soc_pct"] <= cfg.min_soc_pct + 0.5
    return rows
```
- If `battery_low` is true during Renewable mode, the UI shows a small amber note "Battery near reserve — grid assist may be needed". The **mode itself does not change** (mode comes only from the official rules).
- Starting SoC is a number the user can change on the page (default 80%).

---

## 12. Step 9 — Persistence (light, never blocking)

The brief lists Stratus and Data Store, and "end-to-end workflow" is judged, so we use them in the smallest sensible way:

| Service | What we store | Why |
|---|---|---|
| **Stratus** | Uploaded CSV, result JSON (`runs/<run_id>.json`) | "store uploaded CSV files in Stratus" |
| **Data Store** (table `forecast_runs`) | `run_id, created_at, source, n_rows, peak_kw, renewable_hours, overload_hours` | Run history list + system log panel |
| **Data Store** (table `system_logs`) | `created_at, level, message` | Feeds the "System logs" box |

`app/persist.py` — one function `save_run_safely(result)` that does the writes inside `try/except` and logs the error instead of raising. Use the Catalyst Python SDK (`zcatalyst_sdk.initialize(req=request)`; check the SDK docs for the exact Data Store insert and Stratus upload calls while implementing). Create the tables and the bucket in the console first (two minutes).

If persistence breaks, the forecast still returns. If time is short, skip Stratus first, then Data Store. Never skip QuickML or the controller.

---

## 13. Step 10 — Dashboard (UI, 10% — but also helps the 35% "functionality" marks)

Plain HTML + JS + Chart.js (vendored file, no build step, no npm). Fast to build, tiny, loads quickly on judges' laptops and phones.

**Layout (top to bottom, mobile-friendly with CSS grid):**
1. **Header strip**: project name, big **state badge** (`MAIN GRID` green / `RENEWABLE STORAGE` blue) for the *current* hour, last run time, QuickML status dot.
2. **Alert banner** (red, only if any `overload`): "Critical Overload: 3 hours ≥ 200 kW (first at 19:00)". Amber banner for data warnings / battery low.
3. **KPI cards**: Peak demand · Hours on battery · Hours on grid · Overload hours · Lowest SoC.
4. **Main chart — Predicted load curve** (line) with:
   - dashed horizontal line at 160 kW (amber) and 200 kW (red),
   - shaded vertical band for 18:00–22:00,
   - points coloured by mode.
5. **Mode timeline strip**: 24 small cells (one per hour) coloured grid/battery, red outline for overload. Hover = reason.
6. **Battery SoC chart** (area) with 10% reserve line.
7. **Input panel**: tabs — *Upload CSV* · *Manual 24-hour form* (pre-filled grid with 24 rows, editable) · *Next 24 h (typical weather)* · *Load demo day*.
8. **Hourly table**: hour, weather, predicted kW, mode, reason, overload, SoC — sortable, scrollable.
9. **Control signals + System log** side by side (signals list from the response; logs from the session).
10. **Data-check card**: shows `quality` (rows, filled values, clipped values, warnings).

**Behaviour rules:**
- On page load → call `/api/demo` and draw everything. The page is never empty.
- Every button shows a loading spinner, and every error shows a human sentence (no stack traces).
- "Download predictions CSV" button (same format as `predictions.csv`) — small touch, big impression.
- Colour is never the only signal (badge text + icon too) for accessibility.

**Shaded 18–22 band (Chart.js plugin, ~10 lines):**
```js
const peakBand = {
  id: "peakBand",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea: a, scales: { x } } = chart;
    const labels = chart.data.labels;                        // e.g. "18:00"
    const i0 = labels.findIndex(l => l.startsWith("18")), i1 = labels.findIndex(l => l.startsWith("22"));
    if (i0 < 0 || i1 < 0) return;
    ctx.save(); ctx.fillStyle = "rgba(59,130,246,0.10)";
    ctx.fillRect(x.getPixelForValue(i0), a.top, x.getPixelForValue(i1) - x.getPixelForValue(i0), a.bottom - a.top);
    ctx.restore();
  }
};
```

---

## 14. Step 11 — Deploy on Catalyst (do a skeleton deploy tonight)

1. Install the Catalyst CLI, `catalyst login`, `catalyst init` inside the repo → add **AppSail**, runtime **Python**, source directory `app/`.
2. Python dependencies must be **inside the source folder** (AppSail zips the folder): `pip install -r app/requirements.txt -t app/`.
   `requirements.txt`: `flask`, `pandas`, `numpy`, `requests`, `zcatalyst-sdk`.
   (If the upload size becomes a problem, replace pandas inside the backend with plain-Python csv + math — the feature maths is small. Only do this if deploy actually fails.)
3. Startup command (console or `app-config.json`): `python3 -u app.py`.
4. Environment variables (console or `app-config.json` → `env_variables`):
   `ZOHO_ACCOUNTS_URL, ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN, QUICKML_ENDPOINT_URL, QUICKML_ENDPOINT_KEY, CATALYST_ORG_ID, CATALYST_ENV`.
5. `catalyst deploy`. Open the AppSail URL in an **incognito window and on your phone** — it must work with no login.
6. Deploy the skeleton (health route + static page) **tonight**, then redeploy after each milestone. Each deploy is cheap when the app is small.
7. Production vs Development: the URL and QuickML `Environment` header differ between them. Pick the one you will submit and test **that** one end to end.
8. Cold start: open the URL a few minutes before judging time and hit `/api/health`.

---

## 15. Testing plan

| Test | How | Done when |
|---|---|---|
| Controller boundaries | `pytest tests/test_controller.py` | all green |
| Feature parity | take 50 train rows → run through `prepare_training` path and through `predict.py` path → features identical (`np.allclose`) | equal |
| `predict.py` contract | `python predict.py --input data/sample_test_input.csv --output predictions.csv`, then `python test_eval.py` | prints `SUCCESS` |
| Messy input | CSV with blank cells, uppercase headers, an extra column, a bad timestamp, shuffled rows | one output row per input row, no crash |
| Row-count edge cases | 1 row, 24 rows, 48 rows, 500 rows, 501 rows | works / clear error for 501 |
| QuickML failure | wrong key on purpose | app shows friendly error, doesn't crash |
| Live URL | incognito + phone + different browser | page loads, demo forecast visible, upload works |
| End-to-end script | `curl -F file=@sample_test_input.csv https://<app-url>/api/forecast` | JSON with 24+ rows |

---

## 16. Timeline (48 hours)

| When | Goal | Output |
|---|---|---|
| **Mon 26 Oct, tonight (3–4 h)** | Catalyst account, EDA, `features.py`, `prepare_training.py`, local lab, upload to QuickML, first published endpoint, `predict.py` working on sample file | endpoint returns numbers; `test_eval.py` SUCCESS (first time) |
| **Tue 27 Oct, morning** | Backend: ingest → features → QuickML → controller → battery. Unit tests. Skeleton deployed on AppSail | `/api/forecast` works on live URL |
| **Tue 27 Oct, afternoon** | Dashboard (chart, badges, banners, input tabs). Preloaded demo | UI usable end to end |
| **Tue 27 Oct, evening** | QuickML tuning round 2 (features/algorithm), persistence (Data Store/Stratus), final model version published | best RMSE locked, `test_eval.py` SUCCESS again |
| **Tue 27 Oct, night** | README, screenshots, clean repo, zip | repo complete |
| **Wed 28 Oct, morning** | Freeze. Full test checklist on the live URL. Fix only bugs | all checks green |
| **Wed 28 Oct, ≥ 6 h before deadline** | **Submit** (URL + repo/zip). Re-open the URL after submitting | done |

If you are 2–3 people: **A** = data + QuickML + predict.py, **B** = backend + controller + tests + deploy, **C** = dashboard + README + demo. Agree on the response JSON in Section 9.2 first, so B and C can work in parallel with a fake JSON file.

**What to cut first if time runs out** (in this order): rolling features → Stratus → Data Store history → run-history UI → typical-weather generator → manual 24-row form. **Never cut**: QuickML endpoint, `predict.py`, controller, live URL, demo day.

---

## 17. Risks and fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| QuickML endpoint request/response format differs from my guess | High | Only `to_payload` and `parse_response` change (two small functions). Check "Test the Model" page first. |
| OAuth token problems (wrong region/scope) | Medium | Make sure accounts domain, API console and Catalyst data centre are the **same region**; scope `QuickML.deployment.READ`; test with curl before coding. |
| Train/inference feature mismatch | Medium | Single `features.py` + parity test. |
| Random vs time split guess wrong | Medium | EDA decision table; avoid `month`, avoid rolling features unless sure. |
| QuickML training slow or quota limit | Medium | Start the first pipeline tonight; keep AutoML result as a safety version; do not retrain endlessly. |
| AppSail package too big | Low–Medium | Pure-Python backend without pandas. |
| Evaluator cannot run predict.py (credentials) | Medium | Ask organisers; env-var plan + proxy route (Section 8.3); put exact run steps at the top of README. |
| Live URL needs login | Low | Test in incognito; check AppSail access settings. |
| Cold start / slow first load | Low | Cache demo result; ping `/api/health` before judging. |
| Last-minute change breaks something | Medium | Freeze 6 h before deadline; tag the repo (`git tag final`). |

---

## 18. README.md outline (required deliverable)

1. One-paragraph summary + live URL.
2. Architecture diagram (copy Section 2) and which Catalyst service does what.
3. How the model was built: features, local lab result, QuickML pipelines tried and their RMSE, published version.
4. Transition rules and our boundary decisions.
5. Battery simulation assumptions.
6. Setup: clone → env variables list (**names only, never values**) → `pip install` → `python predict.py ...` → `python test_eval.py`.
7. How to run the app locally and deploy with `catalyst deploy`.
8. Testing: how to run the tests.
9. Limitations and next steps (honest, short).

---

## 19. Final pre-submission checklist

- [ ] `python test_eval.py` prints **SUCCESS** against the **final** published endpoint
- [ ] `predict.py` works from a fresh clone (no hidden local files)
- [ ] No secrets in the repo (`git grep -i secret`, `.env` in `.gitignore`)
- [ ] Live URL opens in incognito and on phone; demo forecast is visible immediately
- [ ] CSV upload, manual form and typical-day buttons all work on the live URL
- [ ] Overload banner appears when a row ≥ 200 kW (test with a hot-day CSV)
- [ ] All controller unit tests pass
- [ ] README complete, includes env variable names and the RMSE table
- [ ] GitHub repo is public (or `TeamName_Submission.zip` built and opened once to check)
- [ ] Submitted at least 6 hours before the deadline, and the URL re-checked after submission

---

### Last word
We do not win by being the most complicated. We win by being the team whose `predict.py` never fails, whose model has a clean RMSE, whose URL opens instantly, and whose grid rules are exactly right. Build in this order: **endpoint → predict.py → controller → deploy → dashboard → polish.**
