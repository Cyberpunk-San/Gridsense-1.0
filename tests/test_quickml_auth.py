import quickml_client


def test_headers_use_custom_org_id(monkeypatch):
    monkeypatch.setenv("QUICKML_ENDPOINT_KEY", "endpoint-key")
    monkeypatch.setenv("QUICKML_ORG_ID", "org-custom")
    monkeypatch.setenv("QUICKML_ENV", "Production")
    monkeypatch.setattr(quickml_client, "_access_token", lambda: "access-token")

    headers = quickml_client._headers()

    assert headers["Authorization"] == "Zoho-oauthtoken access-token"
    assert headers["X-QUICKML-ENDPOINT-KEY"] == "endpoint-key"
    assert headers["CATALYST-ORG"] == "org-custom"
    assert headers["Environment"] == "Production"


def test_headers_fall_back_to_catalyst_org(monkeypatch):
    monkeypatch.setenv("QUICKML_ENDPOINT_KEY", "endpoint-key")
    monkeypatch.delenv("QUICKML_ORG_ID", raising=False)
    monkeypatch.setenv("X_ZOHO_CATALYST_ORG_ID", "org-catalyst")
    monkeypatch.setattr(quickml_client, "_access_token", lambda: "access-token")

    assert quickml_client._headers()["CATALYST-ORG"] == "org-catalyst"
