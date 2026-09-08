"""Live-tenant integration fixtures.

Everything here is gated on real credentials (marker ``integration``) and runs
only when either client-credentials env vars or a pre-minted access token are
present. The default unit run uses ``-m "not integration"``, so a clean checkout
with no secrets skips the entire directory.

App-only (client_secret) tokens cannot address ``/me``, so user-scoped reads
resolve a principal via ``list_users`` or ``MSGRAPH_TEST_USER_ID`` instead.
"""

from __future__ import annotations

import os

import pytest
from _util import json_content

_CLIENT_CREDS = all(
    os.getenv(k)
    for k in ("MSGRAPH_CLIENT_ID", "MSGRAPH_TENANT_ID", "MSGRAPH_CLIENT_SECRET")
)


@pytest.fixture(scope="session", autouse=True)
def _require_live_credentials():
    if not (_CLIENT_CREDS or os.getenv("MSGRAPH_ACCESS_TOKEN")):
        pytest.skip(
            "Live integration tests need credentials: MSGRAPH_AUTH_MODE=client_secret "
            "with MSGRAPH_CLIENT_ID/MSGRAPH_TENANT_ID/MSGRAPH_CLIENT_SECRET "
            "(or a pre-minted MSGRAPH_ACCESS_TOKEN)",
            allow_module_level=True,
        )


@pytest.fixture
def first_user_id(call):
    """Resolve a real user id for user-scoped reads (app-only safe)."""
    env_id = os.getenv("MSGRAPH_TEST_USER_ID")
    if env_id:
        return env_id
    users = json_content(call("list_users", {"top": 1}))
    assert isinstance(users, list) and users, "no visible users; is the app consented?"
    return users[0]["id"]


@pytest.fixture
def first_group_id(call):
    """Return the first visible group, or skip the requesting test."""
    groups = json_content(call("list_groups", {"top": 5}))
    assert isinstance(groups, list), "list_groups did not return a list"
    if not groups:
        pytest.skip("no visible groups to inspect")
    return groups[0]["id"]
