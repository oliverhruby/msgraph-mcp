"""Reports — Microsoft 365 usage reports. App-only / admin."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync


@graph_tool("reports", "GET", "/reports/getOffice365ActiveUserDetail", delegated=["Reports.Read.All"], application=["Reports.Read.All"])
def get_active_user_report(period: str = "D7"):
    """Get M365 active user detail report. period: 'D7', 'D30', 'D90', 'D180'."""
    def go():
        return run_sync(graph().get(f"/reports/getOffice365ActiveUserDetail(period='{period}')"))
    return go()


@graph_tool("reports", "GET", "/reports/getTeamsUserActivityUserDetail", delegated=["Reports.Read.All"], application=["Reports.Read.All"])
def get_teams_user_activity(period: str = "D7"):
    def go():
        return run_sync(graph().get(f"/reports/getTeamsUserActivityUserDetail(period='{period}')"))
    return go()


@graph_tool("reports", "GET", "/reports/getMailboxUsageDetail", delegated=["Reports.Read.All"], application=["Reports.Read.All"])
def get_mailbox_usage(period: str = "D7"):
    def go():
        return run_sync(graph().get(f"/reports/getMailboxUsageDetail(period='{period}')"))
    return go()


@graph_tool("reports", "GET", "/reports/getOneDriveUsageAccountDetail", delegated=["Reports.Read.All"], application=["Reports.Read.All"])
def get_onedrive_usage(period: str = "D7"):
    def go():
        return run_sync(graph().get(f"/reports/getOneDriveUsageAccountDetail(period='{period}')"))
    return go()


@graph_tool("reports", "GET", "/reports/getSharePointSiteUsageDetail", delegated=["Reports.Read.All"], application=["Reports.Read.All"])
def get_sharepoint_usage(period: str = "D7"):
    def go():
        return run_sync(graph().get(f"/reports/getSharePointSiteUsageDetail(period='{period}')"))
    return go()
