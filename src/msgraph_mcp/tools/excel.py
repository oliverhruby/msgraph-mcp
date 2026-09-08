"""Excel — workbook worksheets, tables, ranges, sessions (in-place via Graph)."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync


def _item_base(file_id: str, workbook_id: str = "workbook"):
    return f"/me/drive/items/{file_id}/{workbook_id}"


@graph_tool("excel", "GET", "/me/drive/items/{id}/workbook/worksheets", delegated=["Files.ReadWrite"])
def list_worksheets(file_id: str):
    """List worksheets in an Excel workbook stored in OneDrive/SharePoint."""
    def go():
        return run_sync(graph().get_all(f"{_item_base(file_id)}/worksheets"))
    return go()


@graph_tool("excel", "GET", "/me/drive/items/{id}/workbook/worksheets/{name}/usedRange", delegated=["Files.ReadWrite"])
def get_used_range(file_id: str, worksheet: str = None):
    """Get the used (data) range of a worksheet."""
    def go():
        if worksheet:
            return run_sync(graph().get(f"{_item_base(file_id)}/worksheets/{worksheet}/usedRange"))
        return run_sync(graph().get(f"{_item_base(file_id)}/worksheets/usedRange"))
    return go()


@graph_tool("excel", "GET", "/me/drive/items/{id}/workbook/worksheets/{name}/range", delegated=["Files.ReadWrite"])
def read_range(file_id: str, address: str, worksheet: str = None):
    """Read cell values from a range. address: e.g. 'A1:C10' or 'A1'."""
    def go():
        path = f"{_item_base(file_id)}"
        if worksheet:
            path = f"{path}/worksheets/{worksheet}/range(address='{address}')"
        else:
            path = f"{path}/worksheets/range(address='{address}')"
        return run_sync(graph().get(path))
    return go()


@graph_tool("excel", "GET", "/me/drive/items/{id}/workbook/tables", delegated=["Files.ReadWrite"])
def list_tables(file_id: str):
    def go():
        return run_sync(graph().get_all(f"{_item_base(file_id)}/tables"))
    return go()


@graph_tool("excel", "GET", "/me/drive/items/{id}/workbook/tables/{tableId}/rows", delegated=["Files.ReadWrite"])
def list_table_rows(file_id: str, table_id: str):
    def go():
        return run_sync(graph().get(f"{_item_base(file_id)}/tables/{table_id}/rows"))
    return go()


@graph_tool("excel", "PATCH", "/me/drive/items/{id}/workbook/worksheets/{name}/range", delegated=["Files.ReadWrite"])
def write_range(file_id: str, address: str, values_json: str, worksheet: str = None):
    """Write values to a range. values_json: JSON 2D array, e.g. '[[\"A\",1],[\"B\",2]]'."""
    def go():
        require_write()
        import json as _json
        try:
            values = _json.loads(values_json)
        except Exception:
            return fail("values_json must be a valid JSON 2D array")
        path = f"{_item_base(file_id)}"
        if worksheet:
            path = f"{path}/worksheets/{worksheet}/range(address='{address}')"
        else:
            path = f"{path}/worksheets/range(address='{address}')"
        return run_sync(graph().patch(path, json={"values": values}))
    return go()


@graph_tool("excel", "POST", "/me/drive/items/{id}/workbook/tables/{tableId}/rows", delegated=["Files.ReadWrite"])
def append_table_row(file_id: str, table_id: str, values_json: str):
    """Append a row to a table. values_json: JSON 1D array of cell values."""
    def go():
        require_write()
        import json as _json
        try:
            values = _json.loads(values_json)
        except Exception:
            return fail("values_json must be a valid JSON array")
        return run_sync(graph().post(f"{_item_base(file_id)}/tables/{table_id}/rows", json={"values": [values]}))
    return go()


@graph_tool("excel", "PATCH", "/me/drive/items/{id}/workbook/tables/{tableId}/rows/itemAt", delegated=["Files.ReadWrite"])
def update_table_row(file_id: str, table_id: str, index: int, values_json: str):
    """Update a table row. index: 0-based row index."""
    def go():
        require_write()
        import json as _json
        try:
            values = _json.loads(values_json)
        except Exception:
            return fail("values_json must be a valid JSON array")
        return run_sync(graph().patch(f"{_item_base(file_id)}/tables/{table_id}/rows/itemAt(index={index})", json={"values": [values]}))
    return go()


@graph_tool("excel", "POST", "/me/drive/items/{id}/workbook/tables", delegated=["Files.ReadWrite"])
def create_table(file_id: str, address: str, has_headers: bool = True):
    """Create a table from a range. address: e.g. 'A1:D10'."""
    def go():
        require_write()
        return run_sync(graph().post(f"{_item_base(file_id)}/tables", json={
            "address": address,
            "hasHeaders": has_headers,
        }))
    return go()


@graph_tool("excel", "POST", "/me/drive/items/{id}/workbook/createSession", delegated=["Files.ReadWrite"])
def create_session(file_id: str, persist_changes: bool = False):
    """Create a persistent Excel session for batch operations. Returns session ID."""
    def go():
        require_write()
        return run_sync(graph().post(f"{_item_base(file_id)}/createSession", json={
            "persistChanges": persist_changes,
        }))
    return go()
