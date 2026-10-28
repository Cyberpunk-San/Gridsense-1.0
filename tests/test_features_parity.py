# tests/test_features_parity.py
# Feature parity test: training path vs inference path must produce identical features
import numpy as np
import pandas as pd
from features import clean, build_features, load_medians
from ml_lab.prepare_training import FEATURES, RAW


def test_feature_parity():
    """Training features (from prepare_training) must match inference features (predict.py path)"""
    # Load train data
    tr = pd.read_csv("data/train_telemetry.csv")

    # --- Training path (from prepare_training.py) ---
    medians = {c: float(pd.to_numeric(tr[c], errors="coerce").median()) for c in RAW}
    tr_clean = tr.dropna(subset=["target_demand_kw"]).drop_duplicates()
    df_train, _ = clean(tr_clean, medians, interpolate=False)
    X_train = build_features(df_train)

    # --- Inference path (from predict.py / app) ---
    # Use a subset of test data
    te = pd.read_csv("data/sample_test_input.csv").head(50)
    medians = load_medians("artifacts/medians.json")
    df_infer, _ = clean(te, medians, interpolate=False)
    X_infer = build_features(df_infer)

    # Check feature names and order match
    assert list(X_train.columns) == FEATURES, "Training feature order mismatch"
    assert list(X_infer.columns) == FEATURES, "Inference feature order mismatch"
    assert list(X_train.columns) == list(X_infer.columns), "Feature columns differ between train/infer"

    # Check dtypes match
    for c in FEATURES:
        assert X_train[c].dtype == X_infer[c].dtype, f"Dtype mismatch for {c}"

    print("✓ Feature names, order, and dtypes match")


def test_same_input_same_output():
    """Same input row processed through train path and infer path must give same features"""
    # Create a test row
    test_row = pd.DataFrame([{
        "timestamp": "2024-01-01 18:00:00",
        "ambient_temp_c": 25.0,
        "humidity_pct": 60.0,
        "solar_irradiance_wm2": 100.0,
    }])

    medians = load_medians("artifacts/medians.json")

    # Process through clean + build_features (inference path)
    df1, _ = clean(test_row, medians, interpolate=False)
    X1 = build_features(df1)

    # Process again (should be deterministic)
    df2, _ = clean(test_row, medians, interpolate=False)
    X2 = build_features(df2)

    # Should be identical
    assert np.allclose(X1.values, X2.values), "Non-deterministic feature generation"
    print("✓ Same input produces identical features")


def test_no_nan_in_features():
    """Features must never contain NaN"""
    te = pd.read_csv("data/sample_test_input.csv")
    medians = load_medians("artifacts/medians.json")
    df, _ = clean(te, medians, interpolate=False)
    X = build_features(df)

    assert not X.isna().any().any(), "Features contain NaN values"
    print("✓ No NaN in features")


if __name__ == "__main__":
    test_feature_parity()
    test_same_input_same_output()
    test_no_nan_in_features()
    print("\nAll feature parity tests passed!")