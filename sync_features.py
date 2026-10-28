#!/usr/bin/env python3
# sync_features.py - Copy root features.py to app/ before every deploy
# Run this before: catalyst deploy

import shutil
from pathlib import Path

root_features = Path("features.py")
app_features = Path("app/features.py")

if not root_features.exists():
    print(f"ERROR: {root_features} not found")
    exit(1)

shutil.copy2(root_features, app_features)
print(f"✓ Copied {root_features} → {app_features}")

# Also copy artifacts
for artifact in ["medians.json", "feature_order.json"]:
    src = Path("artifacts") / artifact
    dst = Path("app/artifacts") / artifact
    if src.exists():
        shutil.copy2(src, dst)
        print(f"✓ Copied {src} → {dst}")
    else:
        print(f"⚠ {src} not found (run prepare_training.py first)")