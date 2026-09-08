"""Unit tests for GraphClient against a mocked HTTP transport (respx).

Auth is stubbed so no MSAL token acquisition or network I/O ever happens.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
import respx

from msgraph_mcp.graph_client import API_VERSION, GraphClient, GraphError

BASE = "https://graph.microsoft.com"


@pytest.fixture
def auth():
    return SimpleNamespace(
        base_url=BASE,
        acquire_token=lambda: "tok-x",
    )


@pytest.fixture
def client(auth):
    return GraphClient(auth)


def _url(path: str, version: str = API_VERSION) -> str:
    return f"{BASE}/{version}{path}"


@respx.mock
async def test_get_returns_json_with_bearer_header(client):
    route = respx.get(_url("/me")).mock(return_value=httpx.Response(200, json={"displayName": "T"}))
    result = await client.get("/me")
    assert result == {"displayName": "T"}
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer tok-x"
    assert request.headers["content-type"] == "application/json"
    assert request.headers["accept"] == "application/json"


@respx.mock
async def test_post_sends_json_body(client):
    respx.post(_url("/me/messages")).mock(return_value=httpx.Response(201, json={"id": "1"}))
    result = await client.post("/me/messages", json={"subject": "hi"})
    assert result == {"id": "1"}
    sent = json.loads(respx.calls.last.request.content)
    assert sent == {"subject": "hi"}


@respx.mock
async def test_beta_url_version(client):
    route = respx.get(_url("/me/messages", version="beta")).mock(return_value=httpx.Response(200, json={}))
    await client.get("/me/messages", beta=True)
    assert "/beta/me/messages" in str(route.calls.last.request.url)


@respx.mock
async def test_graph_error_carries_status_url_and_message(client):
    respx.get(_url("/me")).mock(
        return_value=httpx.Response(400, json={"error": {"message": "Bad request"}})
    )
    with pytest.raises(GraphError) as e:
        await client.get("/me")
    assert e.value.status == 400
    assert e.value.url == _url("/me")
    assert "Bad request" in str(e.value)


@respx.mock
async def test_non_json_error_body_is_wrapped(client):
    respx.get(_url("/me")).mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(GraphError) as e:
        await client.get("/me")
    assert e.value.body == {"error": {"message": "boom"}}


@respx.mock
async def test_throttle_retries_then_succeeds(client):
    route = respx.get(_url("/me")).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={"error": {}}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    result = await client.get("/me")
    assert result == {"ok": True}
    assert len(route.calls) == 2


@respx.mock
async def test_max_retries_exceeded(client):
    respx.get(_url("/me")).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={"error": {}})
            for _ in range(4)
        ]
    )
    with pytest.raises(GraphError) as e:
        await client.get("/me")
    assert e.value.status == 429
    assert "Max retries exceeded" in str(e.value)


@respx.mock
async def test_get_all_follows_nextlink(client):
    page2_url = _url("/users/page2")
    respx.get(_url("/users")).mock(
        return_value=httpx.Response(
            200,
            json={"value": [{"id": "1"}], "@odata.nextLink": page2_url},
        )
    )
    respx.get(page2_url).mock(return_value=httpx.Response(200, json={"value": [{"id": "2"}]}))
    result = await client.get_all("/users")
    assert [x["id"] for x in result] == ["1", "2"]


@respx.mock
async def test_get_all_respects_max_pages(client):
    route = respx.get(_url("/users")).mock(
        return_value=httpx.Response(
            200,
            json={"value": [{"id": "x"}], "@odata.nextLink": _url("/users")},
        )
    )
    result = await client.get_all("/users", max_pages=2)
    assert len(result) == 2
    assert len(route.calls) == 2


@respx.mock
async def test_get_delta_parses_deltalink(client):
    respx.get(_url("/users/delta")).mock(
        return_value=httpx.Response(
            200,
            json={
                "value": [{"id": "1"}],
                "@odata.deltaLink": _url("/users/delta") + "?$deltatoken=NEW&x=1",
            },
        )
    )
    items, token = await client.get_delta("/users")
    assert [x["id"] for x in items] == ["1"]
    assert token == "NEW"


@respx.mock
async def test_get_delta_with_existing_token(client):
    route = respx.get(_url("/users/delta") + "?%24deltatoken=X").mock(
        return_value=httpx.Response(200, json={"value": []})
    )
    items, token = await client.get_delta("/users", delta_token="X")
    assert items == []
    assert token is None
    assert "%24deltatoken=X" in str(route.calls.last.request.url)


@respx.mock
async def test_batch_posts_and_returns_responses(client):
    respx.post(_url("/$batch")).mock(
        return_value=httpx.Response(200, json={"responses": [{"id": "1", "status": 200, "body": {}}]})
    )
    result = await client.batch([{"id": "1", "method": "GET", "url": "/me"}])
    assert len(result) == 1
    sent = json.loads(respx.calls.last.request.content)
    assert sent["requests"][0]["url"] == "/me"


async def test_batch_rejects_more_than_twenty(client):
    with pytest.raises(ValueError, match="maximum of 20"):
        await client.batch([{"id": str(i), "method": "GET", "url": "/me"} for i in range(21)])


@respx.mock
async def test_absolute_url_passthrough(client):
    absolute = "https://other.example.com/somewhere"
    route = respx.get(absolute).mock(return_value=httpx.Response(200, json={"x": 1}))
    result = await client.get(absolute)
    assert result == {"x": 1}
    assert route.calls.last.request.url == absolute


@respx.mock
async def test_transport_error_retries_then_raises(client):
    respx.get(_url("/me")).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(httpx.ConnectError):
        await client.get("/me")


@respx.mock
async def test_upload_puts_raw_bytes_with_content_type(client):
    route = respx.put(_url("/me/drive/items/1:/test.txt:/content")).mock(
        return_value=httpx.Response(201, json={"id": "file-1", "name": "test.txt"})
    )
    result = await client.put(
        "/me/drive/items/1:/test.txt:/content",
        content=b"hello",
        headers={"Content-Type": "text/plain"},
    )
    assert result == {"id": "file-1", "name": "test.txt"}
    request = route.calls.last.request
    assert request.content == b"hello"
    assert request.headers["content-type"] == "text/plain"
    assert request.headers["authorization"] == "Bearer tok-x"


@respx.mock
async def test_delete_and_patch_pass_method_through(client):
    respx.delete(_url("/me/messages/1")).mock(return_value=httpx.Response(204, content=b""))
    assert await client.delete("/me/messages/1") == {}
    respx.patch(_url("/me/messages/1")).mock(
        return_value=httpx.Response(200, json={"subject": "changed"})
    )
    assert await client.patch("/me/messages/1", json={"subject": "changed"}) == {"subject": "changed"}
