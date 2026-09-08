"""Microsoft Graph authentication via MSAL.

Supports: interactive (PKCE), device code, client secret, certificate,
on-behalf-of, managed identity, and pre-existing token.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import msal

logger = logging.getLogger("msgraph_mcp.auth")

GRAPH_BASE_URLS = {
    "global": "https://graph.microsoft.com",
    "us_gov_l4": "https://graph.microsoft.us",
    "us_gov_l5": "https://dod-graph.microsoft.us",
    "china": "https://microsoftgraph.chinacloudapi.cn",
    "germany": "https://graph.microsoft.de",
}

AUTHORITY_URLS = {
    "global": "https://login.microsoftonline.com",
    "us_gov_l4": "https://login.microsoftonline.us",
    "us_gov_l5": "https://login.microsoftonline.us",
    "china": "https://login.chinacloudapi.cn",
    "germany": "https://login.microsoftonline.de",
}

DEFAULT_DELEGATED_SCOPES = [
    "User.Read",
    "User.ReadBasic.All",
    "Mail.Read",
    "Mail.Send",
    "Calendars.ReadWrite",
    "Contacts.Read",
    "Files.ReadWrite",
    "Sites.Read.All",
    "Chat.Read",
    "ChatMessage.Read",
    "ChatMessage.Send",
    "Team.ReadBasic.All",
    "Channel.ReadBasic.All",
    "Tasks.ReadWrite",
    "Notes.ReadWrite",
    "People.Read",
    "Presence.ReadWrite",
    "OnlineMeetings.ReadWrite",
    "Directory.Read.All",
    "DeviceManagementApps.Read.All",
    "DeviceManagementManagedDevices.Read.All",
    "SecurityIncident.Read.All",
    "AuditLog.Read.All",
    "Reports.Read.All",
    "AccessReview.Read.All",
    "RoleManagement.Read.Directory",
]


class AuthManager:
    """Manages MSAL token acquisition and caching for Microsoft Graph."""

    def __init__(self):
        self.client_id = os.getenv("MSGRAPH_CLIENT_ID", "")
        self.tenant_id = os.getenv("MSGRAPH_TENANT_ID", "common")
        self.client_secret = os.getenv("MSGRAPH_CLIENT_SECRET", "")
        self.cert_path = os.getenv("MSGRAPH_CERT_PATH", "")
        self.cert_password = os.getenv("MSGRAPH_CERT_PASSWORD", "")
        self.auth_mode = os.getenv("MSGRAPH_AUTH_MODE", "interactive")
        self.cloud = os.getenv("MSGRAPH_CLOUD", "global")
        self.pre_token = os.getenv("MSGRAPH_ACCESS_TOKEN", "")
        self.token_cache_path = os.getenv(
            "MSGRAPH_TOKEN_CACHE_PATH",
            str(Path.home() / ".msgraph-mcp" / "token_cache.json"),
        )
        self.base_url = os.getenv("MSGRAPH_BASE_URL", GRAPH_BASE_URLS.get(self.cloud, GRAPH_BASE_URLS["global"]))
        self.extra_scopes = [
            s.strip()
            for s in os.getenv("MSGRAPH_SCOPES", "").split(",")
            if s.strip()
        ]

        self.authority = f"{AUTHORITY_URLS.get(self.cloud, AUTHORITY_URLS['global'])}/{self.tenant_id}"
        self._cache = msal.SerializableTokenCache()
        self._load_cache()
        self._app: msal.ClientApplication | None = None

    # ------------------------------------------------------------------
    # Cache persistence
    # ------------------------------------------------------------------
    def _load_cache(self):
        if os.path.exists(self.token_cache_path):
            try:
                data = Path(self.token_cache_path).read_text(encoding="utf-8")
                self._cache.deserialize(data)
                logger.info("Loaded token cache from %s", self.token_cache_path)
            except Exception:
                logger.warning("Failed to load token cache", exc_info=True)

    def _save_cache(self):
        if self._cache.has_state_changed:
            Path(self.token_cache_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.token_cache_path).write_text(self._cache.serialize(), encoding="utf-8")
            logger.info("Saved token cache to %s", self.token_cache_path)

    # ------------------------------------------------------------------
    # App factory
    # ------------------------------------------------------------------
    def _get_app(self) -> msal.ClientApplication:
        if self._app is not None:
            return self._app

        if self.auth_mode in ("client-secret", "certificate", "obo"):
            credential = self._build_credential()
            self._app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=credential,
                token_cache=self._cache,
            )
        else:
            self._app = msal.PublicClientApplication(
                self.client_id,
                authority=self.authority,
                token_cache=self._cache,
            )
        return self._app

    def _build_credential(self) -> str | dict:
        if self.auth_mode == "certificate" and self.cert_path:
            cert_data = Path(self.cert_path).read_text(encoding="utf-8")
            credential: dict[str, Any] = {"private_key": cert_data}
            if self.cert_password:
                credential["passphrase"] = self.cert_password
            return credential
        return self.client_secret

    # ------------------------------------------------------------------
    # Scope resolution
    # ------------------------------------------------------------------
    def _scopes(self, explicit: list[str] | None = None) -> list[str]:
        if explicit:
            return explicit
        if self.extra_scopes:
            return self.extra_scopes
        if self.auth_mode in ("client-secret", "certificate", "managed-identity"):
            return ["https://graph.microsoft.com/.default"]
        return DEFAULT_DELEGATED_SCOPES

    # ------------------------------------------------------------------
    # Token acquisition
    # ------------------------------------------------------------------
    def acquire_token_silent(self) -> str | None:
        app = self._get_app()
        scopes = self._scopes()

        if self.auth_mode in ("client-secret", "certificate", "managed-identity"):
            result = app.acquire_token_silent(scopes, account=None)
        else:
            accounts = app.get_accounts()
            if accounts:
                result = app.acquire_token_silent(scopes, account=accounts[0])
            else:
                result = None

        if result and "access_token" in result:
            self._save_cache()
            return result["access_token"]
        return None

    def acquire_token_interactive(self) -> str:
        app = self._get_app()
        assert isinstance(app, msal.PublicClientApplication)
        result = app.acquire_token_interactive(
            scopes=self._scopes(),
            login_hint=os.getenv("MSGRAPH_LOGIN_HINT"),
        )
        self._save_cache()
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"Interactive auth failed: {result.get('error')}: {result.get('error_description')}")

    def acquire_token_device_code(self) -> str:
        app = self._get_app()
        assert isinstance(app, msal.PublicClientApplication)
        flow = app.initiate_device_flow(scopes=self._scopes())
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow initiation failed: {flow}")
        print(f"\n{flow['message']}\n", file=__import__("sys").stderr)
        result = app.acquire_token_by_device_flow(flow)
        self._save_cache()
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"Device code auth failed: {result.get('error')}: {result.get('error_description')}")

    def acquire_token_client_credentials(self) -> str:
        app = self._get_app()
        result = app.acquire_token_for_client(scopes=self._scopes())
        self._save_cache()
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"Client credentials auth failed: {result.get('error')}: {result.get('error_description')}")

    def acquire_token_by_certificate(self) -> str:
        return self.acquire_token_client_credentials()

    def acquire_token_on_behalf_of(self, user_token: str) -> str:
        app = self._get_app()
        assert isinstance(app, msal.ConfidentialClientApplication)
        result = app.acquire_token_on_behalf_of(user_token, scopes=self._scopes())
        self._save_cache()
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"OBO auth failed: {result.get('error')}: {result.get('error_description')}")

    def acquire_token_managed_identity(self) -> str:
        app = self._get_app()
        result = app.acquire_token_for_client(scopes=self._scopes())
        self._save_cache()
        if "access_token" in result:
            return result["access_token"]
        raise RuntimeError(f"Managed identity auth failed: {result.get('error')}: {result.get('error_description')}")

    def acquire_token(self) -> str:
        """Main entry point — try silent first, then fall back to interactive."""
        if self.pre_token:
            return self.pre_token

        token = self.acquire_token_silent()
        if token:
            return token

        dispatch = {
            "interactive": self.acquire_token_interactive,
            "device-code": self.acquire_token_device_code,
            "client-secret": self.acquire_token_client_credentials,
            "certificate": self.acquire_token_by_certificate,
            "obo": self.acquire_token_on_behalf_of,
            "managed-identity": self.acquire_token_managed_identity,
            "token": lambda: self.pre_token,
        }

        handler = dispatch.get(self.auth_mode)
        if handler is None:
            raise ValueError(f"Unknown auth mode: {self.auth_mode}")
        return handler()

    # ------------------------------------------------------------------
    # Token info
    # ------------------------------------------------------------------
    def get_account_info(self) -> dict:
        app = self._get_app()
        accounts = app.get_accounts()
        if accounts:
            return {
                "username": accounts[0].get("username"),
                "home_account_id": accounts[0].get("home_account_id"),
            }
        return {"auth_mode": self.auth_mode, "tenant_id": self.tenant_id}
