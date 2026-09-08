"""Read-only integration tests against a real Microsoft Graph tenant.

Marker: ``integration``. These hit live endpoints backed by the user's Entra app
permissions; nothing here mutates tenant data. Run locally with client-secret env
vars or from the integration workflow (manual / post-merge until it graduates to
a required check).
"""

from __future__ import annotations

import os

import pytest
from _util import json_content

pytestmark = pytest.mark.integration

needs_delegated = pytest.mark.skipif(
    os.getenv("MSGRAPH_AUTH_MODE", "interactive") == "client_secret",
    reason="requires delegated (interactive) auth; app-only tokens cannot address /me",
)


def test_list_users_returns_directory(call):
    result = call("list_users", {"top": 5})
    users = json_content(result)
    assert isinstance(users, list)
    assert users, "expected at least one visible user"
    assert all(u.get("id") and u.get("userPrincipalName") for u in users)


def test_get_user_roundtrip(call, first_user_id):
    result = call("get_user", {"user_id": first_user_id})
    profile = json_content(result)
    assert isinstance(profile, dict)
    assert profile.get("id") == first_user_id
    assert profile.get("userPrincipalName")


def test_get_user_licenses(call, first_user_id):
    result = call("get_user_licenses", {"user_id": first_user_id})
    assert isinstance(json_content(result), list)


def test_get_user_presence(call, first_user_id):
    result = call("get_user_presence", {"user_id": first_user_id})
    presence = json_content(result)
    assert isinstance(presence, dict)
    assert "availability" in presence
    assert "activity" in presence


def test_list_groups(call):
    result = call("list_groups", {"top": 5})
    groups = json_content(result)
    assert isinstance(groups, list)
    assert all(g.get("id") and g.get("displayName") for g in groups)


def test_group_members_list(call, first_group_id):
    result = call("list_group_members", {"group_id": first_group_id, "top": 5})
    assert isinstance(json_content(result), list)


def test_root_site(call):
    result = call("get_root_site")
    site = json_content(result)
    assert isinstance(site, dict)
    assert site.get("id") and site.get("webUrl")


def test_search_sites(call):
    result = call("search_sites", {"query": "communication"})
    sites = json_content(result)
    assert isinstance(sites, list)


@needs_delegated
def test_get_my_profile(call):
    result = call("get_my_profile")
    profile = json_content(result)
    assert isinstance(profile, dict)
    assert profile.get("userPrincipalName")


@needs_delegated
def test_list_root_files(call):
    result = call("list_root_files", {"top": 5})
    files = json_content(result)
    assert isinstance(files, list)
