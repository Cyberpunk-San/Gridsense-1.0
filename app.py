"""Catalyst AppSail entrypoint.

This project has both a package directory named `app/` and a root file named
`app.py`. Importing `from app.app import app` from the root file creates a
name collision in Catalyst where Python resolves the top-level `app` module to
this file instead of the package directory.

To avoid that recursion, this launcher loads the real Flask app directly from
`app/app.py` by file path instead of importing the package by name.
"""

import importlib.util
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
APP_PACKAGE_DIR = ROOT_DIR / "app"
APP_FILE = APP_PACKAGE_DIR / "app.py"

if not APP_FILE.exists():
    raise FileNotFoundError(f"Missing app entry file: {APP_FILE}")

spec = importlib.util.spec_from_file_location("gridsense_app_module", APP_FILE)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load app entry file: {APP_FILE}")

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
app = module.app


if __name__ == "__main__":
    port = int(os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", "9000"))
    app.run(host="0.0.0.0", port=port)
