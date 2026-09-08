"""Batch — execute up to 20 Graph requests in a single $batch call."""

from __future__ import annotations

import json

from ._common import fail, graph, graph_tool, run_sync


@graph_tool("batch", "POST", "/$batch", delegated=[], application=[])
def batch_request(requests_json: str):
    """Execute up to 20 Graph requests in one round trip.
    requests_json: JSON array of {id, method, url, body?, headers?}.
    Relative URLs like '/me/messages' are relative to the selected API version.
    """
    def go():
        try:
            requests = json.loads(requests_json)
        except Exception:
            return fail("requests_json must be a valid JSON array")

        if not isinstance(requests, list):
            return fail("requests_json must be a JSON array")
        if len(requests) > 20:
            return fail("$batch supports a maximum of 20 requests")

        # Normalize URLs: strip API version prefix if present
        for req in requests:
            url = req.get("url", "")
            for prefix in ("/v1.0", "/beta"):
                if url.startswith(prefix):
                    req["url"] = url[len(prefix):]
                    break

        return run_sync(graph().batch(requests))
    return go()
