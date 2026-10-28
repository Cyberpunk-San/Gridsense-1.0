import app.persist as persist


def test_memory_fallback_keeps_recent_run_and_log(monkeypatch):
    persist._runs_cache.clear()
    persist._logs_cache.clear()

    monkeypatch.setitem(__import__("sys").modules, "zcatalyst_sdk", None)
    run = {
        "run_id": "run-test-1",
        "source": "test",
        "rows": [],
        "summary": {
            "peak_kw": 100.0,
            "renewable_hours": 0,
            "grid_hours": 0,
            "overload_hours": 0,
            "min_soc_pct": 80.0,
        },
    }

    persist.save_run_safely(run)
    persist.log_system("info", "test lifecycle event")

    assert persist.get_run("run-test-1") == run
    logs = persist.get_logs()
    assert any(log["message"] == "test lifecycle event" for log in logs)
