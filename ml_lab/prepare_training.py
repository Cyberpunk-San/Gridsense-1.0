# ml_lab/prepare_training.py
# Creates train_engineered.csv for QuickML upload and saves medians/feature_order
import json
import os
import sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
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