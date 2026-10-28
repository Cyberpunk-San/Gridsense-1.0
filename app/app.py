# app/app.py
# Flask backend for HackSphere 3.0 - serves API and static dashboard

import os
import sys
import uuid
import datetime as dt
from pathlib import Path
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(PROJECT_ROOT))

try:  # Supports both `python app/app.py` and `from app.app import app`.
    from .ingest import ingest_raw, MAX_ROWS
    from .quickml_client import predict_rows
    from .controller import decide_all
    from .battery import simulate
    from . import persist
except ImportError:  # pragma: no cover - direct AppSail entry point
    from app.ingest import ingest_raw, MAX_ROWS
    from app.quickml_client import predict_rows
    from app.controller import decide_all
    from app.battery import simulate
    from app import persist


app = Flask(__name__, static_folder="static", static_url_path="")
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# In-memory demo cache
_demo_cache = {"data": None, "ts": 0}


@app.get("/")
def home():
    return send_from_directory(APP_DIR / "static", "index.html")


@app.get("/api/health")
def health():
    return jsonify(status="ok", version="1.0")


def run_forecast(raw: pd.DataFrame, source: str):
    """Core forecast pipeline: ingest → QuickML → controller → battery → persist"""
    feature_rows, rows, quality = ingest_raw(raw, source)

    # Get predictions from QuickML
    preds = predict_rows(feature_rows)

    # Attach predictions to rows
    for i, p in enumerate(preds):
        rows[i]["predicted_kw"] = round(float(p), 2)
        rows[i]["_raw_kw"] = float(p)

    # Apply transition controller
    rows, signals = decide_all(rows)

    # Simulate battery
    rows = simulate(rows)

    total_energy_kwh = round(sum(r["_raw_kw"] for r in rows), 2)

    # Remove internal fields
    for r in rows:
        r.pop("_raw_kw", None)

    # Build summary
    summary = {
        "peak_kw": max(r["predicted_kw"] for r in rows),
        "peak_timestamp": max(rows, key=lambda r: r["predicted_kw"])["timestamp"],
        # Inputs are hourly, so the sum of hourly kW readings represents kWh
        # across the forecast horizon. Keep this explicit rather than labelling
        # instantaneous power as energy in the UI.
        "total_energy_kwh": total_energy_kwh,
        "forecast_hours": len(rows),
        "renewable_hours": sum(r["mode"] == "RENEWABLE_STORAGE" for r in rows),
        "grid_hours": sum(r["mode"] == "MAIN_GRID" for r in rows),
        "overload_hours": sum(r["overload"] for r in rows),
        "min_soc_pct": min(r["soc_pct"] for r in rows),
    }

    result = {
        "run_id": f"{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:4]}",
        "source": source,
        "quality": quality,
        "rows": rows,
        "signals": signals,
        "summary": summary,
    }

    persist.save_run_safely(result)
    persist.log_system(
        "info",
        f"Forecast completed: {source} · {len(rows)} hours · peak {summary['peak_kw']:.1f} kW",
    )
    return result


@app.post("/api/forecast")
def forecast():
    try:
        if "file" in request.files:
            raw = pd.read_csv(request.files["file"])
            src = "csv_upload"
        else:
            payload = request.get_json(force=True)
            if not isinstance(payload, dict) or "rows" not in payload:
                raise ValueError("JSON request must contain a 'rows' array.")
            if not isinstance(payload["rows"], list):
                raise ValueError("'rows' must be an array.")
            raw = pd.DataFrame(payload["rows"])
            src = "manual_form"
        return jsonify(run_forecast(raw, src))
    except ValueError as e:
        persist.log_system("warning", f"Forecast rejected: {e}")
        return jsonify(error=str(e)), 400
    except Exception as e:
        app.logger.exception("forecast failed")
        persist.log_system("error", f"Forecast failed: {str(e)[:180]}")
        return jsonify(error="Forecast service temporarily unavailable.", detail=str(e)[:200]), 502


@app.get("/api/demo")
def demo():
    global _demo_cache
    import time
    now = time.time()
    if _demo_cache["data"] and now - _demo_cache["ts"] < 600:
        return jsonify(_demo_cache["data"])

    raw = pd.read_csv(PROJECT_ROOT / "data" / "demo_day.csv")
    result = run_forecast(raw, "demo_day")
    _demo_cache = {"data": result, "ts": now}
    return jsonify(result)


@app.get("/api/typical-day")
def typical_day():
    """Build a 24-hour typical day from average hourly profiles in training data"""
    date_str = request.args.get("date", dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    tr = pd.read_csv(PROJECT_ROOT / "data" / "train_telemetry.csv", parse_dates=["timestamp"])

    # Average weather by hour of day
    hourly_avg = tr.groupby(tr.timestamp.dt.hour)[["ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"]].mean()

    rows = []
    for h in range(24):
        base_date = pd.Timestamp(date_str)
        ts = base_date + pd.to_timedelta(h, unit="h")
        avg = hourly_avg.loc[h] if h in hourly_avg.index else hourly_avg.mean()
        rows.append({
            "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "ambient_temp_c": round(float(avg["ambient_temp_c"]), 2),
            "humidity_pct": round(float(avg["humidity_pct"]), 2),
            "solar_irradiance_wm2": round(float(avg["solar_irradiance_wm2"]), 2),
        })

    raw = pd.DataFrame(rows)
    result = run_forecast(raw, "typical_day")
    result["note"] = "Estimated typical weather from training data averages"
    return jsonify(result)


@app.get("/api/runs")
def list_runs():
    runs = persist.get_runs(50)
    return jsonify(runs=runs)


@app.get("/api/runs/<run_id>")
def get_run(run_id):
    run = persist.get_run(run_id)
    if not run:
        return jsonify(error="Run not found"), 404
    return jsonify(run)


@app.get("/api/logs")
def get_logs():
    logs = persist.get_logs(50)
    return jsonify(logs=logs)


@app.post("/api/predict_csv")
def predict_csv_proxy():
    """Backup proxy for predict.py when it can't reach QuickML directly"""
    # Simple shared-key auth
    auth = request.headers.get("X-PREDICT-KEY")
    if auth != os.getenv("PREDICT_PROXY_KEY"):
        return jsonify(error="Unauthorized"), 401

    try:
        raw = pd.read_csv(request.files["file"])
        if len(raw) > 2000:
            return jsonify(error="Too many rows (max 2000)"), 400
        result = run_forecast(raw, "predict_proxy")
        # Return just the predictions in predict.py format
        preds = [{"timestamp": r["timestamp"], "target_demand_kw": r["predicted_kw"]} for r in result["rows"]]
        return jsonify(predictions=preds)
    except Exception as e:
        app.logger.exception("predict_csv failed")
        return jsonify(error=str(e)), 500


if __name__ == "__main__":
    port = int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", 9000))
    app.run(host="0.0.0.0", port=port)
