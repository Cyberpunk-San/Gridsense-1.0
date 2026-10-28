# app/battery.py
# Battery state-of-charge simulation for the dashboard
# The statement asks for "battery state-of-charge" but gives no battery data.
# This is a clearly-labelled simulation with configurable assumptions.

from dataclasses import dataclass


@dataclass
class BatteryCfg:
    capacity_kwh: float = 1200.0      # tune so a typical evening does not hit the floor
    soc0_pct: float = 80.0            # starting state of charge
    min_soc_pct: float = 10.0
    max_discharge_kw: float = 250.0
    max_charge_kw: float = 80.0
    efficiency: float = 0.95
    pv_kwp: float = 120.0             # simulated solar array that charges the battery


def simulate(rows, cfg: BatteryCfg = BatteryCfg()):
    """
    Simulate battery SoC over 24 hours.
    Modifies rows in place: adds route contribution fields, soc_pct,
    battery_kw, and battery_low.
    Returns rows.
    """
    soc = cfg.capacity_kwh * cfg.soc0_pct / 100
    floor = cfg.capacity_kwh * cfg.min_soc_pct / 100

    for r in rows:
        # Solar charging from irradiance (simplified: irradiance W/m2 -> kW for 120 kWp array)
        pv_kw = cfg.pv_kwp * r["solar_irradiance_wm2"] / 1000.0
        charge_kw = min(pv_kw * cfg.efficiency, cfg.max_charge_kw)
        discharge_kw = 0.0

        if r["mode"] == "RENEWABLE_STORAGE":
            # Discharge to meet demand, limited by max discharge and remaining SoC above floor
            available = max(soc - floor, 0.0)
            remaining_demand = max(r["_raw_kw"] - pv_kw, 0.0)
            discharge_kw = min(remaining_demand, cfg.max_discharge_kw, available)

        # 1-hour step: kW ≈ kWh
        soc = min(max(soc + charge_kw - discharge_kw, floor if discharge_kw else 0), cfg.capacity_kwh)

        r["soc_pct"] = round(100 * soc / cfg.capacity_kwh, 1)
        r["battery_kw"] = round(charge_kw - discharge_kw, 1)      # + charging, − discharging
        r["solar_kw"] = round(min(r["_raw_kw"], pv_kw), 1)
        r["battery_supply_kw"] = round(discharge_kw, 1)
        r["grid_kw"] = round(max(r["_raw_kw"] - r["solar_kw"] - discharge_kw, 0.0), 1)
        r["battery_low"] = r["soc_pct"] <= cfg.min_soc_pct + 0.5

    return rows