import sys
import types

import app.persist as persist


class FakeTable:
    def __init__(self):
        self.rows = []

    def insert_row(self, row):
        self.rows.append(dict(row))

    def get_all_rows(self, max_rows=50):
        return list(self.rows)[-max_rows:]

    def get_row_by_id(self, row_id):
        return next((row for row in self.rows if row.get("run_id") == row_id), None)


class FakeDatastore:
    def __init__(self):
        self.tables = {}

    def table(self, name):
        return self.tables.setdefault(name, FakeTable())


class FakeFolder:
    def __init__(self):
        self.uploads = {}

    def upload_file(self, file_name, file_content):
        self.uploads[file_name] = file_content


class FakeFileStore:
    def __init__(self):
        self.folders = {}

    def folder(self, name):
        return self.folders.setdefault(name, FakeFolder())


class FakeApp:
    def __init__(self):
        self._datastore = FakeDatastore()
        self._filestore = FakeFileStore()

    def datastore(self):
        return self._datastore

    def filestore(self):
        return self._filestore


def install_fake_sdk(monkeypatch):
    fake_app = FakeApp()
    module = types.SimpleNamespace(initialize=lambda: fake_app)
    monkeypatch.setitem(sys.modules, "zcatalyst_sdk", module)
    return fake_app


def sample_run(run_id="run-catalyst-1"):
    return {
        "run_id": run_id,
        "source": "test",
        "rows": [{"predicted_kw": 100}],
        "summary": {
            "peak_kw": 100,
            "renewable_hours": 0,
            "grid_hours": 1,
            "overload_hours": 0,
            "min_soc_pct": 80,
        },
    }


def test_catalyst_run_is_written_to_data_store_and_stratus(monkeypatch):
    fake = install_fake_sdk(monkeypatch)
    persist.save_run_safely(sample_run())

    stored = fake.datastore().table("forecast_runs").rows
    assert stored[0]["run_id"] == "run-catalyst-1"
    uploads = fake.filestore().folder("forecast-files").uploads
    assert "runs/run-catalyst-1.json" in uploads


def test_catalyst_run_and_logs_can_be_read(monkeypatch):
    fake = install_fake_sdk(monkeypatch)
    persist.save_run_safely(sample_run("run-read-1"))
    persist.log_system("info", "stored event")

    assert persist.get_run("run-read-1")["run_id"] == "run-read-1"
    assert persist.get_runs()[0]["run_id"] == "run-read-1"
    assert persist.get_logs()[0]["message"] == "stored event"


def test_log_cache_is_bounded(monkeypatch):
    persist._logs_cache.clear()
    monkeypatch.setitem(sys.modules, "zcatalyst_sdk", None)
    for index in range(250):
        persist.log_system("info", f"event-{index}")

    assert len(persist._logs_cache) == 200
    assert persist._logs_cache[0]["message"] == "event-50"
