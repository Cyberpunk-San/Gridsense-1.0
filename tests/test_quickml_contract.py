import os

import pytest

import quickml_client


def test_payload_preserves_feature_rows():
    rows = [{"hour": 1, "ambient_temp_c": 20.0}, {"hour": 2, "ambient_temp_c": 21.0}]
    assert quickml_client.to_payload(rows) == {"data": rows}


@pytest.mark.parametrize(
    "response",
    [
        {"predictions": [1, 2.5]},
        {"data": [{"target_demand_kw": 1}, {"target_demand_kw": 2.5}]},
        {"result": [1, 2.5]},
        [1, 2.5],
    ],
)
def test_parse_response_accepts_supported_shapes(response):
    assert quickml_client.parse_response(response) == [1.0, 2.5]


def test_parse_response_rejects_missing_prediction_key():
    with pytest.raises((KeyError, TypeError)):
        quickml_client.parse_response({"predictions": [{"wrong": 1}]})


def test_access_token_is_cached(monkeypatch):
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"access_token": "token", "expires_in": 3600}

    monkeypatch.setattr(quickml_client.requests, "post", lambda *args, **kwargs: calls.append(1) or Response())
    monkeypatch.setenv("ZOHO_CLIENT_ID", "id")
    monkeypatch.setenv("ZOHO_CLIENT_SECRET", "secret")
    monkeypatch.setenv("ZOHO_REFRESH_TOKEN", "refresh")
    quickml_client._tok.update(value=None, exp=0)

    assert quickml_client._access_token() == "token"
    assert quickml_client._access_token() == "token"
    assert len(calls) == 1


def test_predict_rows_batches_requests_and_preserves_order(monkeypatch):
    calls = []

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def __init__(self, values):
            self.values = values

        def json(self):
            return {"predictions": self.values}

    def post(url, json, headers, timeout):
        calls.append(json["data"])
        return Response([row["value"] for row in json["data"]])

    monkeypatch.setenv("QUICKML_ENDPOINT_URL", "https://example.test/predict")
    monkeypatch.setattr(quickml_client, "_headers", lambda: {})
    monkeypatch.setattr(quickml_client.requests, "post", post)
    rows = [{"value": i} for i in range(5)]

    assert quickml_client.predict_rows(rows, batch=2) == [0, 1, 2, 3, 4]
    assert [len(call) for call in calls] == [2, 2, 1]


def test_predict_rows_retries_transient_failure(monkeypatch):
    attempts = []

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"predictions": [42]}

    def post(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("temporary network failure")
        return Response()

    monkeypatch.setenv("QUICKML_ENDPOINT_URL", "https://example.test/predict")
    monkeypatch.setattr(quickml_client, "_headers", lambda: {})
    monkeypatch.setattr(quickml_client.requests, "post", post)
    monkeypatch.setattr(quickml_client.time, "sleep", lambda _: None)

    assert quickml_client.predict_rows([{"value": 1}], retries=2) == [42.0]
    assert len(attempts) == 2


def test_predict_rows_raises_after_retry_budget(monkeypatch):
    monkeypatch.setenv("QUICKML_ENDPOINT_URL", "https://example.test/predict")
    monkeypatch.setattr(quickml_client, "_headers", lambda: {})
    monkeypatch.setattr(quickml_client.requests, "post", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(quickml_client.time, "sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="down"):
        quickml_client.predict_rows([{"value": 1}], retries=2)
