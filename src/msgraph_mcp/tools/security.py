"""Security — alerts, incidents, secure scores. App-only / admin."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync, to_query


@graph_tool("security", "GET", "/security/alerts_v2", delegated=["SecurityAlert.Read.All"], application=["SecurityAlert.Read.All"])
def list_security_alerts(top: int = None, filter: str = None):
    """List Microsoft 365 Defender alerts (v2)."""
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/security/alerts_v2", params=params))
    return go()


@graph_tool("security", "GET", "/security/alerts_v2/{id}", delegated=["SecurityAlert.Read.All"], application=["SecurityAlert.Read.All"])
def get_security_alert(alert_id: str):
    def go():
        return run_sync(graph().get(f"/security/alerts_v2/{alert_id}"))
    return go()


@graph_tool("security", "GET", "/security/incidents", delegated=["SecurityIncident.Read.All"], application=["SecurityIncident.Read.All"])
def list_security_incidents(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/security/incidents", params=params))
    return go()


@graph_tool("security", "GET", "/security/incidents/{id}", delegated=["SecurityIncident.Read.All"], application=["SecurityIncident.Read.All"])
def get_security_incident(incident_id: str):
    def go():
        return run_sync(graph().get(f"/security/incidents/{incident_id}"))
    return go()


@graph_tool("security", "GET", "/security/secureScores", delegated=["SecurityEvents.Read.All"], application=["SecurityEvents.Read.All"])
def list_secure_scores(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/security/secureScores", params=params))
    return go()


@graph_tool("security", "GET", "/security/secureScoreControlProfiles", delegated=["SecurityEvents.Read.All"], application=["SecurityEvents.Read.All"])
def list_secure_score_controls(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/security/secureScoreControlProfiles", params=params))
    return go()
