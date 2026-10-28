# GridSense — Smart Energy Microgrid Forecasting & Control

**Forecast the load. Direct the energy.**

GridSense is a microgrid forecasting and control application that predicts hourly electricity demand, converts forecasts into grid and storage decisions, simulates battery and solar dispatch, and presents the results in a web dashboard.

Unlike a standalone forecasting demo, GridSense connects demand prediction to an explicit control layer that determines how the microgrid should respond to changing demand.

## Live Demo

- **Application:** https://gridsense-50047192240.development.catalystappsail.in/
- **Health Check:** https://gridsense-50047192240.development.catalystappsail.in/api/health

Open the application and use the available demo or sample forecast flow to explore the predicted load, operating mode, battery state of charge, and overload status.

## Features

- **24-hour demand forecasting:** Predicts hourly electricity demand using a QuickML regression endpoint.
- **Flexible data ingestion:** Accepts telemetry through manual input and CSV uploads.
- **Data validation:** Validates timestamps and numeric inputs before processing.
- **Feature engineering:** Constructs the fixed feature vector required by the forecasting model.
- **Intelligent dispatch:** Selects renewable-storage or main-grid mode based on predicted demand and time of day.
- **Overload detection:** Raises a critical-overload alert when predicted demand reaches the configured threshold.
- **Battery simulation:** Models battery state of charge and solar contribution.
- **Interactive dashboard:** Displays demand forecasts and operational decisions.
- **Run history:** Stores forecast runs and logs for subsequent review.

## How It Works

```text
Telemetry / CSV Upload
          |
          v
Input Validation and Cleaning
          |
          v
Feature Engineering
          |
          v
QuickML Demand Prediction
          |
          v
Controller Decision Engine
          |
          v
Battery and Solar Simulation
          |
          v
Dashboard, Logs, and Run History
```

The Flask backend coordinates data processing, model inference, controller decisions, battery simulation, and persistence. The frontend presents the resulting forecast and operating state.

## Controller Logic

GridSense applies explicit threshold- and time-based rules to determine the operating mode.

| Condition | Decision |
|---|---|
| Predicted demand > 160 kW | Renewable Storage mode |
| Hour is between 18:00 and 22:00, inclusive | Renewable Storage mode |
| Predicted demand ≥ 200 kW | Critical Overload alert |
| Otherwise | Main Grid mode |

The critical-overload condition is evaluated independently of the selected dispatch mode.

These rules are designed to be transparent and testable, with the same thresholds used by the controller and dashboard.

## Forecasting and Model Evaluation

The following validation metrics are reported by the project:

| Metric | Value |
|---|---:|
| MAE | 7.1238 |
| MSE | 81.3541 |
| RMSE | 9.0197 kW |
| RMSLE | 0.0663 |
| R² | 0.9671 |
| MAPE | 5.0864% |

These values represent validation performance and should not be interpreted as guaranteed results on unseen evaluation data.

MAPE can be sensitive to actual demand values near zero. It should therefore be considered alongside MAE, RMSE, and R².

## Model Input Contract

The forecasting pipeline uses a fixed set of 12 input features. The feature order must remain consistent during training and inference.

| No. | Feature | Description |
|---:|---|---|
| 1 | `ambient_temp_c` | Ambient temperature in Celsius |
| 2 | `humidity_pct` | Relative humidity |
| 3 | `solar_irradiance_wm2` | Solar irradiance |
| 4 | `hour` | Hour of the day |
| 5 | `dow` | Day of the week |
| 6 | `is_weekend` | Weekend indicator |
| 7 | `hour_sin` | Sine encoding of the hour |
| 8 | `hour_cos` | Cosine encoding of the hour |
| 9 | `is_peak_window` | Peak-period indicator |
| 10 | `cdd` | Cooling degree days |
| 11 | `hdd` | Heating degree days |
| 12 | `temp_x_hum` | Temperature-humidity interaction feature |

**Target variable:** `target_demand_kw`

The target represents the demand value being predicted. It must not be included among the input features.

The QuickML response is read from the first value in its `result` array.

## Architecture

### System Components

| Component | Responsibility |
|---|---|
| Frontend dashboard | Displays forecasts and operating decisions |
| Python and Flask backend | Handles API requests and coordinates processing |
| Input pipeline | Parses and validates telemetry |
| Feature engineering | Constructs the model input vector |
| Zoho Catalyst QuickML | Provides demand prediction |
| Controller engine | Determines dispatch mode and overload status |
| Battery simulator | Simulates battery, solar, and grid contribution |
| Persistence layer | Manages run history and logs |
| Zoho Catalyst AppSail | Hosts the backend application |

### Technology Stack

- Python 3
- Flask
- Pandas
- NumPy
- scikit-learn
- Zoho Catalyst QuickML
- Zoho Catalyst AppSail
- Chart.js

## Repository Structure

```text
GridSense/
├── app/
│   ├── app.py              # Flask routes and application orchestration
│   ├── quickml_client.py   # QuickML request and response handling
│   ├── controller.py       # Dispatch and overload rules
│   ├── battery.py          # Battery and solar simulation
│   ├── ingest.py           # Input parsing and feature engineering
│   ├── persist.py          # Run history and logs
│   └── static/             # Dashboard assets
├── ml_lab/                  # Model selection and validation
├── data/                    # Demo and training telemetry
├── tests/                   # Automated tests
└── reference_design.png     # Project visual/reference
```

## Getting Started

### Prerequisites

- Python 3
- pip
- Git
- QuickML and Catalyst configuration for live model inference

### 1. Clone the Repository

```bash
git clone <repository-url>
cd GridSense
```

Replace `<repository-url>` with the URL of your repository.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Environment

**Windows**

```bash
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Set the required environment variables before running the application.

```env
QUICKML_ENDPOINT_URL=
QUICKML_ENDPOINT_KEY=
ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
```

Optional variables:

```env
QUICKML_ORG_ID=
X_ZOHO_CATALYST_ORG_ID=
PREDICT_PROXY_KEY=
```

Use your own credentials in the environment. **Never commit API keys, OAuth tokens, or client secrets to GitHub.**

### 6. Run the Application

```bash
python app/app.py
```

Open the following URL in your browser:

```text
http://localhost:9000/
```

## Deployment

GridSense is designed for deployment using Zoho Catalyst AppSail, with QuickML providing model inference.

The deployed application exposes a health endpoint for checking service availability:

```text
/api/health
```

When QuickML is unavailable or unconfigured, the application may use a deterministic local forecasting fallback. During evaluation, verify which inference path is active and distinguish fallback predictions from live QuickML results.

## Testing

Run the automated test suite:

```bash
pytest -q
```

Check the local health endpoint:

```bash
curl http://localhost:9000/api/health
```

The documented test coverage includes:

- API behaviour
- Persistence and fallback handling
- Model pipeline correctness
- Feature-engineering consistency
- QuickML payload contract
- Controller decision logic
- Battery simulation

## Limitations and Evaluation Notes

- Validation metrics are not guaranteed hidden-test or competition scores.
- The local forecasting fallback is distinct from successful live QuickML inference.
- Battery and renewable dispatch outputs are simulations, not measurements from a physical microgrid.
- Controller thresholds represent the project's configured policy and should be validated before use in a real energy system.

## Project Information

**Project:** GridSense — Smart Energy Microgrid Forecasting & Control  
**Team:** `ummm....`  
**Contact:** sansritimishra2427@gmail.com  
**Deployment:** Zoho Catalyst

GridSense demonstrates an end-to-end workflow connecting hourly demand forecasting, transparent dispatch decisions, battery simulation, and dashboard-based monitoring in a single application.
