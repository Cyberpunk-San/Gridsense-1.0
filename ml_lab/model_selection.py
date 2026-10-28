"""Leakage-safe local model selection shared by experiments and the evaluator fallback."""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score


def chronological_split(
    frame: pd.DataFrame, validation_fraction: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a timestamp-ordered fit/validation split without row-order leakage."""
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if "timestamp" not in frame.columns:
        raise ValueError("frame must contain a timestamp column")
    ordered = frame.copy()
    ordered["_parsed_timestamp"] = pd.to_datetime(
        ordered["timestamp"], errors="coerce"
    )
    if ordered["_parsed_timestamp"].isna().any():
        raise ValueError("timestamp contains unreadable values")
    ordered = ordered.sort_values("_parsed_timestamp", kind="stable")
    cutoff = int(len(ordered) * (1 - validation_fraction))
    if cutoff <= 0 or cutoff >= len(ordered):
        raise ValueError("validation split would be empty")
    return (
        ordered.iloc[:cutoff].drop(columns="_parsed_timestamp"),
        ordered.iloc[cutoff:].drop(columns="_parsed_timestamp"),
    )


def candidate_models() -> dict:
    """Return deterministic candidates whose scores are comparable on the same folds."""
    return {
        "extra_trees": ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=2,
            max_features=1.0,
            n_jobs=-1,
            random_state=42,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=400,
            learning_rate=0.03,
            max_depth=3,
            min_samples_leaf=3,
            random_state=42,
        ),
    }


def chronological_rmse(model, features, target, folds: int = 5):
    """Measure RMSE with forward-only folds; lower is better."""
    splitter = TimeSeriesSplit(n_splits=folds)
    scores = -cross_val_score(
        model,
        features,
        target,
        cv=splitter,
        scoring="neg_root_mean_squared_error",
        n_jobs=1,
    )
    return scores
