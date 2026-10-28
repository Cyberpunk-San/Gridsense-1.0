# tests/test_controller.py
# Unit tests for transition controller - 20% marks, must be perfect
import pytest
from app.controller import decide


@pytest.mark.parametrize("kw,hour,mode,overload", [
    # MAIN_GRID cases (demand ≤ 160, outside 18-22)
    (100, 12, "MAIN_GRID", False),
    (160.0, 12, "MAIN_GRID", False),            # exactly 160 → grid
    (100, 17, "MAIN_GRID", False),
    (100, 23, "MAIN_GRID", False),
    (120, 0, "MAIN_GRID", False),
    (150, 6, "MAIN_GRID", False),

    # RENEWABLE_STORAGE by threshold only (>160, outside window)
    (160.01, 12, "RENEWABLE_STORAGE", False),
    (199.99, 3, "RENEWABLE_STORAGE", False),

    # RENEWABLE_STORAGE by window only (≤160, inside 18-22)
    (100, 18, "RENEWABLE_STORAGE", False),      # window start inclusive
    (100, 22, "RENEWABLE_STORAGE", False),      # window end inclusive
    (150, 20, "RENEWABLE_STORAGE", False),

    # RENEWABLE_STORAGE by both (>160, inside 18-22)
    (170, 18, "RENEWABLE_STORAGE", False),
    (250, 20, "RENEWABLE_STORAGE", True),

    # Overload cases (≥200, independent of mode)
    (200.0, 3, "RENEWABLE_STORAGE", True),      # exactly 200 → overload
    (200.0, 18, "RENEWABLE_STORAGE", True),
    (250, 3, "RENEWABLE_STORAGE", True),
])
def test_rules(kw, hour, mode, overload):
    m, _, o = decide(kw, hour)
    assert (m, o) == (mode, overload), f"Failed for kw={kw}, hour={hour}: got {(m, o)}, expected {(mode, overload)}"


def test_decide_all_basic():
    from app.controller import decide_all
    rows = [
        {"timestamp": "2024-01-01 12:00:00", "hour": 12, "_raw_kw": 100, "predicted_kw": 100},
        {"timestamp": "2024-01-01 18:00:00", "hour": 18, "_raw_kw": 180, "predicted_kw": 180},
        {"timestamp": "2024-01-01 19:00:00", "hour": 19, "_raw_kw": 190, "predicted_kw": 190},
        {"timestamp": "2024-01-01 23:00:00", "hour": 23, "_raw_kw": 90, "predicted_kw": 90},
    ]
    rows, signals = decide_all(rows)

    assert rows[0]["mode"] == "MAIN_GRID"
    assert rows[1]["mode"] == "RENEWABLE_STORAGE"
    assert rows[2]["mode"] == "RENEWABLE_STORAGE"
    assert rows[3]["mode"] == "MAIN_GRID"

    # Should have signals for mode changes
    assert len(signals) >= 2  # START_ON_GRID, SWITCH_TO_BATTERY, SWITCH_TO_GRID
    assert signals[0]["command"] == "START_ON_GRID"
    assert signals[1]["command"] == "SWITCH_TO_BATTERY"
    assert signals[2]["command"] == "SWITCH_TO_GRID"


def test_overload_signal():
    from app.controller import decide_all
    rows = [
        {"timestamp": "2024-01-01 12:00:00", "hour": 12, "_raw_kw": 210, "predicted_kw": 210},
    ]
    rows, signals = decide_all(rows)
    assert rows[0]["overload"] == True
    assert any(s["command"] == "CRITICAL_OVERLOAD_ALERT" for s in signals)