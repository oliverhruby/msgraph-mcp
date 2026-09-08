"""Unit tests for AuthManager: cloud maps, environment wiring, scope resolution,
token plumbing, and the client-credential error path.

No test here performs a network round-trip; token acquisition is exercised only
in the modes that fail fast offline or are stubbed.
"""

from __future__ import annotations

import msal
import pytest

from msgraph_mcp.auth import AUTHORITY_URLS, DEFAULT_DELEGATED_SCOPES, GRAPH_BASE_URLS, AuthManager


@pytest.fixture(autouse=True)
def _isolated_token_cache(monkeypatch, tmp_path):
    """Keep every test away from the developer's real ~/.msgraph-mcp cache."""
    monkeypatch.setenv("MSGRAPH_TOKEN_CACHE_PATH", str(tmp_path / "token_cache.json"))


def test_cloud_maps_cover_all_sovereigns():
    assert set(GRAPH_BASE_URLS) == {"global", "us_gov_l4", "us_gov_l5", "china", "germany"}
    assert set(AUTHORITY_URLS) == set(GRAPH_BASE_URLS)
    assert GRAPH_BASE_URLS["global"] == "https://graph.microsoft.com"
    assert GRAPH_BASE_URLS["us_gov_l4"] == "https://graph.microsoft.us"
    assert AUTHORITY_URLS["global"] == "https://login.microsoftonline.com"


def test_auth_mode_accepts_documented_underscore_values(monkeypatch, tmp_path):
    """README documents device_code/client_secret/... ; the code dispatches on hyphens."""
    import msgraph_mcp.auth as auth_mod

    cases = {
        "device_code": "device-code",
        "client_secret": "client-secret",
        "certificate": "certificate",
        "managed_identity": "managed-identity",
        "managed_identity_user": "managed-identity",
        "pre_token": "pre-token",
        "interactive": "interactive",
        "device-code": "device-code",
    }
    assert auth_mod._normalize_auth_mode("DEVICE_CODE") == "device-code"
    for raw, expected in cases.items():
        assert auth_mod._normalize_auth_mode(raw) == expected
        monkeypatch.setenv("MSGRAPH_AUTH_MODE", raw)
        assert AuthManager().auth_mode == expected


def test_default_delegated_scopes_marked_core():
    for scope in ("User.Read", "Mail.Read", "Mail.Send", "Calendars.ReadWrite",
                  "Files.ReadWrite", "Tasks.ReadWrite", "Directory.Read.All"):
        assert scope in DEFAULT_DELEGATED_SCOPES
    assert "https://graph.microsoft.com/.default" not in DEFAULT_DELEGATED_SCOPES


def test_env_config_mapping(monkeypatch, tmp_path):
    monkeypatch.setenv("MSGRAPH_CLIENT_ID", "11111111-1111-1111-1111-111111111111")
    monkeypatch.setenv("MSGRAPH_TENANT_ID", "22222222-2222-2222-2222-222222222222")
    monkeypatch.setenv("MSGRAPH_AUTH_MODE", "client-secret")
    monkeypatch.setenv("MSGRAPH_CLOUD", "us_gov_l4")
    monkeypatch.setenv("MSGRAPH_ACCESS_TOKEN", "token-abc")
    cache_path = tmp_path / "sub" / "cache.json"
    monkeypatch.setenv("MSGRAPH_TOKEN_CACHE_PATH", str(cache_path))

    am = AuthManager()
    assert am.client_id == "11111111-1111-1111-1111-111111111111"
    assert am.tenant_id == "22222222-2222-2222-2222-222222222222"
    assert am.auth_mode == "client-secret"
    assert am.cloud == "us_gov_l4"
    assert am.pre_token == "token-abc"
    assert am.base_url == GRAPH_BASE_URLS["us_gov_l4"]
    assert am.authority == f"{AUTHORITY_URLS['us_gov_l4']}/22222222-2222-2222-2222-222222222222"
    assert am.token_cache_path == str(cache_path)


def test_defaults_when_env_unset(monkeypatch):
    for key in ("MSGRAPH_CLIENT_ID", "MSGRAPH_TENANT_ID", "MSGRAPH_AUTH_MODE",
                "MSGRAPH_CLOUD", "MSGRAPH_ACCESS_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    am = AuthManager()
    assert am.client_id == ""
    assert am.tenant_id == "common"
    assert am.auth_mode == "interactive"
    assert am.cloud == "global"
    assert am.base_url == GRAPH_BASE_URLS["global"]


def test_scopes_resolution_precedence(monkeypatch):
    am = AuthManager()
    monkeypatch.setattr(am, "extra_scopes", [])
    monkeypatch.setattr(am, "auth_mode", "interactive")
    assert am._scopes(["A", "B"]) == ["A", "B"]  # explicit wins

    monkeypatch.setattr(am, "extra_scopes", ["X.Read"])
    assert am._scopes() == ["X.Read"]  # MSGRAPH_SCOPES overrides defaults
    assert am._scopes(["Y"]) == ["Y"]  # ...but explicit still wins

    monkeypatch.setattr(am, "extra_scopes", [])
    monkeypatch.setattr(am, "auth_mode", "client-secret")
    assert am._scopes() == ["https://graph.microsoft.com/.default"]

    monkeypatch.setattr(am, "auth_mode", "certificate")
    assert am._scopes() == ["https://graph.microsoft.com/.default"]

    monkeypatch.setattr(am, "auth_mode", "interactive")
    assert am._scopes() == DEFAULT_DELEGATED_SCOPES


def test_acquire_token_returns_pre_token_without_app(monkeypatch):
    monkeypatch.setenv("MSGRAPH_ACCESS_TOKEN", "pre-token")
    monkeypatch.setenv("MSGRAPH_AUTH_MODE", "token")
    am = AuthManager()
    assert am.acquire_token() == "pre-token"


def test_unknown_auth_mode_raises(monkeypatch):
    am = AuthManager()
    monkeypatch.setattr(am, "auth_mode", "spaceship")
    monkeypatch.setattr(am, "acquire_token_silent", lambda: None)
    with pytest.raises(ValueError, match="Unknown auth mode"):
        am.acquire_token()


def test_client_credentials_missing_token_raises(monkeypatch):
    from types import SimpleNamespace

    am = AuthManager()
    failing_app = SimpleNamespace(
        acquire_token_for_client=lambda *a, **k: {"error": "invalid_client", "error_description": "nope"}
    )
    monkeypatch.setattr(am, "_get_app", lambda: failing_app)
    with pytest.raises(RuntimeError, match="invalid_client"):
        am.acquire_token_client_credentials()


def test_cache_save_and_load_roundtrip(monkeypatch, tmp_path):
    cache_path = tmp_path / "token_cache.json"
    monkeypatch.setenv("MSGRAPH_TOKEN_CACHE_PATH", str(cache_path))

    am = AuthManager()
    monkeypatch.setattr(am._cache, "has_state_changed", True)
    am._save_cache()
    assert cache_path.exists()

    am2 = AuthManager()
    captured: list[str] = []
    am2._cache.deserialize = lambda data: captured.append(data)
    am2._load_cache()
    assert captured, "cache file should be loaded on construction"


def test_cache_save_skipped_without_state_change(monkeypatch, tmp_path):
    cache_path = tmp_path / "not_created.json"
    monkeypatch.setenv("MSGRAPH_TOKEN_CACHE_PATH", str(cache_path))
    am = AuthManager()
    am._save_cache()
    assert not cache_path.exists()


def test_load_missing_cache_is_silent(monkeypatch, tmp_path):
    monkeypatch.setenv("MSGRAPH_TOKEN_CACHE_PATH", str(tmp_path / "missing.json"))
    am = AuthManager()
    assert am._cache is not None


def test_get_account_info_fallback_without_accounts(monkeypatch):
    monkeypatch.setenv("MSGRAPH_CLIENT_ID", "44444444-4444-4444-4444-444444444444")
    monkeypatch.setenv("MSGRAPH_TENANT_ID", "common")
    am = AuthManager()
    info = am.get_account_info()
    assert info["auth_mode"] == "interactive"
    assert info["tenant_id"] == "common"


def test_get_account_info_uses_first_account(monkeypatch):
    from types import SimpleNamespace

    am = AuthManager()
    app = SimpleNamespace(
        get_accounts=lambda: [{"username": "u@c.com", "home_account_id": "acc-1"}]
    )
    monkeypatch.setattr(am, "_get_app", lambda: app)
    info = am.get_account_info()
    assert info["username"] == "u@c.com"
    assert info["home_account_id"] == "acc-1"


def test_obo_and_managed_fail_fast_on_bad_token(monkeypatch):
    class _FakeCCA(msal.ConfidentialClientApplication):
        def __init__(self):
            self._scopes_called = []

        def acquire_token_on_behalf_of(self, *a, **k):
            return {"error": "E"}

        def acquire_token_for_client(self, *a, **k):
            return {"error": "E"}

    am = AuthManager()
    monkeypatch.setattr(am, "_get_app", lambda: _FakeCCA())
    with pytest.raises(RuntimeError):
        am.acquire_token_on_behalf_of("jwt")
    with pytest.raises(RuntimeError):
        am.acquire_token_managed_identity()


def test_public_app_used_default(monkeypatch):
    monkeypatch.setenv("MSGRAPH_AUTH_MODE", "interactive")
    monkeypatch.setenv("MSGRAPH_CLIENT_ID", "55555555-5555-5555-5555-555555555555")
    am = AuthManager()
    assert isinstance(am._get_app(), msal.PublicClientApplication)


def test_confidential_app_for_client_secret(monkeypatch):
    monkeypatch.setenv("MSGRAPH_AUTH_MODE", "client-secret")
    monkeypatch.setenv("MSGRAPH_CLIENT_ID", "33333333-3333-3333-3333-333333333333")
    monkeypatch.setenv("MSGRAPH_CLIENT_SECRET", "s3cr3t")
    am = AuthManager()
    assert isinstance(am._get_app(), msal.ConfidentialClientApplication)


def test_certificate_credential_builds_dict(monkeypatch, tmp_path):
    cert = tmp_path / "cert.pem"
    cert.write_text("-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----", encoding="utf-8")
    monkeypatch.setenv("MSGRAPH_AUTH_MODE", "certificate")
    monkeypatch.setenv("MSGRAPH_CERT_PATH", str(cert))
    monkeypatch.setenv("MSGRAPH_CERT_PASSWORD", "pw")
    am = AuthManager()
    cred = am._build_credential()
    assert cred["private_key"].startswith("-----BEGIN PRIVATE KEY-----")
    assert cred["passphrase"] == "pw"


def test_certificate_without_password(monkeypatch, tmp_path):
    cert = tmp_path / "cert.pem"
    cert.write_text("key", encoding="utf-8")
    monkeypatch.setenv("MSGRAPH_AUTH_MODE", "certificate")
    monkeypatch.setenv("MSGRAPH_CERT_PATH", str(cert))
    am = AuthManager()
    cred = am._build_credential()
    assert cred == {"private_key": "key"}


def test_batch_scopes_via_extra_env(monkeypatch):
    monkeypatch.setenv("MSGRAPH_SCOPES", " A.Read , B.Read ")
    am = AuthManager()
    assert am.extra_scopes == ["A.Read", "B.Read"]
    monkeypatch.setattr(am, "auth_mode", "interactive")
    assert am._scopes() == ["A.Read", "B.Read"]
