# app/config.py
# All tunable configuration values in one place

import os

# Catalyst / QuickML
ZOHO_ACCOUNTS_URL = os.getenv("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
QUICKML_ENDPOINT_URL = os.getenv("QUICKML_ENDPOINT_URL")
QUICKML_ENDPOINT_KEY = os.getenv("QUICKML_ENDPOINT_KEY")
QUICKML_ORG_ID = os.getenv("QUICKML_ORG_ID")
QUICKML_ENV = os.getenv("QUICKML_ENV", "Development")

# App limits
MAX_ROWS_PER_REQUEST = 500
DEMO_CACHE_TTL_SECONDS = 600  # 10 minutes

# Battery simulation defaults
BATTERY_CAPACITY_KWH = 1200.0
BATTERY_SOC0_PCT = 80.0
BATTERY_MIN_SOC_PCT = 10.0
BATTERY_MAX_DISCHARGE_KW = 250.0
BATTERY_MAX_CHARGE_KW = 80.0
BATTERY_EFFICIENCY = 0.95
BATTERY_PV_KWP = 120.0

# Transition controller thresholds
PEAK_START_HOUR = 18
PEAK_END_HOUR = 22
STORAGE_THRESHOLD_KW = 160.0
OVERLOAD_THRESHOLD_KW = 200.0

# Feature engineering
CDD_BASE = 22.0
HDD_BASE = 18.0

# Feature order (must match training)
FEATURE_ORDER = [
    "ambient_temp_c", "humidity_pct", "solar_irradiance_wm2",
    "hour", "dow", "is_weekend", "hour_sin", "hour_cos", "is_peak_window",
    "cdd", "hdd", "temp_x_hum"
]