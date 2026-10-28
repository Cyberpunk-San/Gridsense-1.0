#!/usr/bin/env python3
# download_chartjs.py - Download Chart.js v4.4.2 UMD bundle
# Run this once to get the vendor file

import urllib.request
from pathlib import Path

url = "https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"
dest = Path("app/static/vendor/chart.umd.min.js")

dest.parent.mkdir(parents=True, exist_ok=True)

print(f"Downloading Chart.js from {url}...")
urllib.request.urlretrieve(url, dest)
print(f"✓ Saved to {dest} ({dest.stat().st_size} bytes)")