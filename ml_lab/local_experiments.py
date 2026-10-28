# ml_lab/local_experiments.py
# Local lab to find best features and model family before QuickML
# Purpose: find out which features and which model family win, so QuickML work becomes a copy job

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from model_selection import candidate_models, chronological_rmse

try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False
    print("LightGBM not installed, skipping LGBM model")

# Load engineered training data
df = pd.read_csv("train_engineered.csv")
y = df.pop("target_demand_kw")
X = df

# IMPORTANT: Based on EDA, this is a CHRONOLOGICAL SPLIT
# Use TimeSeriesSplit to respect temporal order
cv = TimeSeriesSplit(n_splits=5)
print("Using TimeSeriesSplit (chronological split)")

models = {
    "ridge": RidgeCV(alphas=[0.1, 1, 10, 100]),
    "rf": RandomForestRegressor(300, min_samples_leaf=3, n_jobs=-1, random_state=42),
}
models.update(candidate_models())
if HAS_LGBM:
    models["lgbm"] = lgb.LGBMRegressor(
        n_estimators=600, learning_rate=0.03, num_leaves=31,
        subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1
    )

print(f"\n{'Model':<8} {'RMSE':>8} {'±Std':>8}")
print("-" * 28)
for name, m in models.items():
    rmse = chronological_rmse(m, X, y)
    print(f"{name:<8} {rmse.mean():>8.3f} {rmse.std():>8.3f}")

# Feature ablation - test which features help
print("\n=== FEATURE ABLATION (Ridge) ===")
baseline_features = X.columns.tolist()
for feat in baseline_features:
    X_drop = X.drop(columns=[feat])
    rmse = -cross_val_score(RidgeCV(alphas=[0.1, 1, 10, 100]), X_drop, y, cv=cv,
                             scoring="neg_root_mean_squared_error", n_jobs=-1)
    diff = rmse.mean() - (-cross_val_score(RidgeCV(alphas=[0.1, 1, 10, 100]), X, y, cv=cv,
                                             scoring="neg_root_mean_squared_error", n_jobs=-1).mean())
    status = "↑ worse" if diff > 0.01 else "↓ better" if diff < -0.01 else "≈ same"
    print(f"Drop {feat:<18} RMSE: {rmse.mean():.3f} ({status})")

print("\n=== BEST LOCAL RMSE TARGET FOR QUICKML ===")
best_rmse = min(-cross_val_score(m, X, y, cv=cv, scoring="neg_root_mean_squared_error", n_jobs=-1).mean()
                for m in models.values())
print(f"Target RMSE to beat in QuickML: {best_rmse:.3f}")