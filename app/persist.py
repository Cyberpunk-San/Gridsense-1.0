# app/persist.py
# Persistence layer - light, never blocking
# Uses Catalyst Data Store and Stratus (wrapped in try/except)

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-memory fallback when Catalyst services unavailable
_runs_cache = []
_logs_cache = []


def save_run_safely(result):
    """Save run to Data Store and Stratus. Never raises."""
    try:
        # Try Catalyst SDK first
        from zcatalyst_sdk import initialize
        app = initialize()

        # Save to Data Store (table: forecast_runs)
        ds = app.datastore()
        table = ds.table("forecast_runs")
        row = {
            "run_id": result["run_id"],
            "created_at": result["run_id"],  # using run_id as timestamp
            "source": result["source"],
            "n_rows": len(result["rows"]),
            "peak_kw": result["summary"]["peak_kw"],
            "renewable_hours": result["summary"]["renewable_hours"],
            "grid_hours": result["summary"]["grid_hours"],
            "overload_hours": result["summary"]["overload_hours"],
            "min_soc_pct": result["summary"]["min_soc_pct"],
        }
        table.insert_row(row)

        # Save to Stratus (bucket: forecast-files)
        filestore = app.filestore()
        bucket = filestore.folder("forecast-files")
        bucket.upload_file(
            file_name=f"runs/{result['run_id']}.json",
            file_content=json.dumps(result, default=str).encode()
        )
        logger.info(f"Persisted run {result['run_id']} to Catalyst")

    except Exception as e:
        # Fallback to in-memory cache
        logger.warning(f"Catalyst persistence failed, using memory cache: {e}")
        _runs_cache.append(result)
        if len(_runs_cache) > 100:
            _runs_cache.pop(0)


def get_runs(limit=50):
    """Get recent runs from Data Store or cache."""
    try:
        from zcatalyst_sdk import initialize
        app = initialize()
        ds = app.datastore()
        table = ds.table("forecast_runs")
        rows = table.get_all_rows(max_rows=limit)
        return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)
    except Exception:
        return sorted(_runs_cache, key=lambda x: x.get("run_id", ""), reverse=True)[:limit]


def get_run(run_id):
    """Get a specific run by ID."""
    try:
        from zcatalyst_sdk import initialize
        app = initialize()
        ds = app.datastore()
        table = ds.table("forecast_runs")
        row = table.get_row_by_id(run_id)
        return row
    except Exception:
        for r in _runs_cache:
            if r.get("run_id") == run_id:
                return r
        return None


def log_system(level, message):
    """Log to system_logs table or memory cache."""
    entry = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    }
    try:
        from zcatalyst_sdk import initialize
        app = initialize()
        ds = app.datastore()
        table = ds.table("system_logs")
        table.insert_row(entry)
    except Exception:
        _logs_cache.append(entry)
        if len(_logs_cache) > 200:
            _logs_cache.pop(0)


def get_logs(limit=50):
    """Get recent system logs."""
    stored_rows = []
    try:
        from zcatalyst_sdk import initialize
        app = initialize()
        ds = app.datastore()
        table = ds.table("system_logs")
        stored_rows = table.get_all_rows(max_rows=limit) or []
    except Exception:
        stored_rows = []

    # Keep local lifecycle messages visible even when Data Store is available
    # but the current process has not flushed or cannot read the table yet.
    combined = stored_rows + _logs_cache
    seen = set()
    unique = []
    for row in sorted(combined, key=lambda x: x.get("created_at", ""), reverse=True):
        key = (row.get("created_at"), row.get("level"), row.get("message"))
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique[:limit]