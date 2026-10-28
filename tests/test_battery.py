import pytest

from app.battery import BatteryCfg, simulate


def test_dispatch_reconciles_to_predicted_demand():
    rows = [
        {
            "mode": "RENEWABLE_STORAGE",
            "solar_irradiance_wm2": 500.0,
            "_raw_kw": 180.0,
        },
        {
            "mode": "MAIN_GRID",
            "solar_irradiance_wm2": 0.0,
            "_raw_kw": 100.0,
        },
    ]

    simulate(rows, BatteryCfg(capacity_kwh=500, soc0_pct=80, min_soc_pct=10))

    for row in rows:
        supplied = row["grid_kw"] + row["battery_supply_kw"] + row["solar_kw"]
        assert supplied == pytest.approx(row["_raw_kw"], abs=0.2)


def test_solar_is_used_before_battery_discharge():
    rows = [{
        "mode": "RENEWABLE_STORAGE",
        "solar_irradiance_wm2": 1000.0,
        "_raw_kw": 80.0,
    }]

    simulate(rows, BatteryCfg(capacity_kwh=500, soc0_pct=80, min_soc_pct=10, pv_kwp=120))

    assert rows[0]["solar_kw"] == pytest.approx(80.0)
    assert rows[0]["battery_supply_kw"] == 0.0
    assert rows[0]["grid_kw"] == 0.0


def test_battery_never_discharges_below_reserve():
    rows = [{
        "mode": "RENEWABLE_STORAGE",
        "solar_irradiance_wm2": 0.0,
        "_raw_kw": 500.0,
    }]
    cfg = BatteryCfg(
        capacity_kwh=100,
        soc0_pct=20,
        min_soc_pct=10,
        max_discharge_kw=500,
    )

    simulate(rows, cfg)

    assert rows[0]["soc_pct"] >= cfg.min_soc_pct
    assert rows[0]["battery_low"] is True
