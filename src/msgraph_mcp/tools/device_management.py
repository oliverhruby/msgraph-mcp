"""Device management (Intune) — devices, apps, configurations, compliance. App-only."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync, to_query


@graph_tool("device_management", "GET", "/deviceManagement/managedDevices", delegated=["DeviceManagementManagedDevices.Read.All"], application=["DeviceManagementManagedDevices.Read.All"])
def list_managed_devices(top: int = None, filter: str = None, select: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter, "$select": select})
        return run_sync(graph().get_all("/deviceManagement/managedDevices", params=params))
    return go()


@graph_tool("device_management", "GET", "/deviceManagement/managedDevices/{id}", delegated=["DeviceManagementManagedDevices.Read.All"], application=["DeviceManagementManagedDevices.Read.All"])
def get_managed_device(device_id: str):
    def go():
        return run_sync(graph().get(f"/deviceManagement/managedDevices/{device_id}"))
    return go()


@graph_tool("device_management", "GET", "/devices", delegated=["Device.Read.All"], application=["Device.Read.All"])
def list_directory_devices(top: int = None, filter: str = None):
    """List directory (Entra) devices, not Intune-managed devices."""
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/devices", params=params))
    return go()


@graph_tool("device_management", "GET", "/deviceManagement/deviceConfigurations", delegated=["DeviceManagementConfiguration.Read.All"], application=["DeviceManagementConfiguration.Read.All"])
def list_device_configurations(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/deviceManagement/deviceConfigurations", params=params))
    return go()


@graph_tool("device_management", "GET", "/deviceManagement/deviceCompliancePolicies", delegated=["DeviceManagementConfiguration.Read.All"], application=["DeviceManagementConfiguration.Read.All"])
def list_compliance_policies(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/deviceManagement/deviceCompliancePolicies", params=params))
    return go()


@graph_tool("device_management", "GET", "/deviceAppManagement/mobileApps", delegated=["DeviceManagementApps.Read.All"], application=["DeviceManagementApps.Read.All"])
def list_mobile_apps(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/deviceAppManagement/mobileApps", params=params))
    return go()


@graph_tool("device_management", "GET", "/deviceAppManagement/mobileApps/{id}", delegated=["DeviceManagementApps.Read.All"], application=["DeviceManagementApps.Read.All"])
def get_mobile_app(app_id: str):
    def go():
        return run_sync(graph().get(f"/deviceAppManagement/mobileApps/{app_id}"))
    return go()
