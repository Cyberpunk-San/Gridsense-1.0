# ml_lab/eda.py
# Exploratory Data Analysis - run this first to understand the data
import pandas as pd

RAW = ["ambient_temp_c", "humidity_pct", "solar_irradiance_wm2"]

tr = pd.read_csv("data/train_telemetry.csv", parse_dates=["timestamp"])
te = pd.read_csv("data/sample_test_input.csv", parse_dates=["timestamp"])

print("=== BASIC INFO ===")
print(f"Train shape: {tr.shape}")
print(f"Test shape: {te.shape}")
print()
print(f"Train date range: {tr.timestamp.min()} → {tr.timestamp.max()}")
print(f"Test date range:  {te.timestamp.min()} → {te.timestamp.max()}")
print()
print("Train target stats:")
print(tr.target_demand_kw.describe())
print()
print("Missing values in train:")
print(tr.isna().sum())
print()
print("Missing values in test:")
print(te.isna().sum())
print()

# Check time step regularity
d = tr.timestamp.sort_values().diff().dropna()
print(f"Train 1-hour steps: {(d == pd.Timedelta('1h')).mean():.2%}")
dt = te.timestamp.sort_values().diff().dropna()
print(f"Test 1-hour steps:  {(dt == pd.Timedelta('1h')).mean():.2%}")
print()

# Hourly demand pattern
print("=== DEMAND BY HOUR ===")
hourly = tr.groupby(tr.timestamp.dt.hour).target_demand_kw.agg(["mean", "std"]).round(1)
print(hourly)
print()

# Day of week pattern
print("=== DEMAND BY DAY OF WEEK ===")
print(tr.groupby(tr.timestamp.dt.dayofweek).target_demand_kw.mean().round(1))
print()

# Monthly pattern
print("=== DEMAND BY MONTH ===")
print(tr.groupby(tr.timestamp.dt.month).target_demand_kw.mean().round(1))
print()

# Correlation
print("=== CORRELATIONS WITH TARGET ===")
corr = tr[RAW + ["target_demand_kw"]].corr().round(2)
print(corr["target_demand_kw"].drop("target_demand_kw"))
print()

# Threshold stats
print("=== THRESHOLD STATS ===")
print(f"Share >160 kW:  {(tr.target_demand_kw > 160).mean():.3f}")
print(f"Share >=200 kW: {(tr.target_demand_kw >= 200).mean():.3f}")
print()

# Decision table for feature safety
print("=== FEATURE SAFETY DECISION TABLE ===")
print("Train months:", sorted(tr.timestamp.dt.month.unique()))
print("Test months: ", sorted(te.timestamp.dt.month.unique()))
print()
print("→ This is a CHRONOLOGICAL SPLIT (test after train)")
print("→ Month 7 (July) is UNSEEN in training - DO NOT use 'month' feature")
print("→ Hour, dow, weather features are SAFE")
print("→ Data is contiguous hourly - rolling features POSSIBLE but risky")