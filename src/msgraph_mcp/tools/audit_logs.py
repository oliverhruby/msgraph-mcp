"""Audit logs — sign-in logs, audit logs, provisioning logs. App-only / admin."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync, to_query


@graph_tool("audit_logs", "GET", "/auditLogs/signIns", delegated=["AuditLog.Read.All"], application=["AuditLog.Read.All"])
def list_sign_in_logs(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/auditLogs/signIns", params=params))
    return go()


@graph_tool("audit_logs", "GET", "/auditLogs/signIns/{id}", delegated=["AuditLog.Read.All"], application=["AuditLog.Read.All"])
def get_sign_in_log(log_id: str):
    def go():
        return run_sync(graph().get(f"/auditLogs/signIns/{log_id}"))
    return go()


@graph_tool("audit_logs", "GET", "/auditLogs/directoryAudits", delegated=["AuditLog.Read.All"], application=["AuditLog.Read.All"])
def list_directory_audit_logs(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/auditLogs/directoryAudits", params=params))
    return go()


@graph_tool("audit_logs", "GET", "/auditLogs/provisioning", delegated=["AuditLog.Read.All"], application=["AuditLog.Read.All"])
def list_provisioning_logs(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/auditLogs/provisioning", params=params))
    return go()
