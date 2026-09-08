"""Shared data models for Microsoft Graph resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphResponse:
    value: list[dict] = field(default_factory=list)
    odata_next_link: str | None = None
    odata_count: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> GraphResponse:
        return cls(
            value=data.get("value", []),
            odata_next_link=data.get("@odata.nextLink"),
            odata_count=data.get("@odata.count"),
        )


@dataclass
class DeltaResponse:
    items: list[dict] = field(default_factory=list)
    delta_link: str | None = None
    next_link: str | None = None
    deleted: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> DeltaResponse:
        items = []
        deleted = []
        for item in data.get("value", []):
            if "@removed" in item:
                deleted.append(item)
            else:
                items.append(item)
        return cls(
            items=items,
            delta_link=data.get("@odata.deltaLink"),
            next_link=data.get("@odata.nextLink"),
            deleted=deleted,
        )


@dataclass
class BatchRequest:
    id: str
    method: str
    url: str
    body: dict | None = None
    headers: dict | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"id": self.id, "method": self.method, "url": self.url}
        if self.body:
            d["body"] = self.body
        if self.headers:
            d["headers"] = self.headers
        return d


@dataclass
class BatchResponse:
    id: str
    status: int
    body: dict | None = None
    headers: dict | None = None
