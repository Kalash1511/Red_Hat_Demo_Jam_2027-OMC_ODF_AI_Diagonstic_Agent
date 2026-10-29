from __future__ import annotations

from langchain_core.tools import StructuredTool

from src.omc_client import OMCClient
from src.ceph.ceph_pod_commands import CephPodCommands


def create_ceph_pod_tools(client: OMCClient) -> list[StructuredTool]:
    """Create LangChain tools for Ceph pod diagnostics in openshift-storage."""

    commands = CephPodCommands(client)

    # Keep container_name strictly required in the tool schema, so the agent
    # must discover/select a valid container before requesting its logs.
    def get_container_logs(
        pod_name: str,
        container_name: str,
        tail: int = 100,
    ) -> str:
        """Get filtered troubleshooting logs from one named pod container."""
        result = commands.get_pod_logs(
            pod_name=pod_name,
            container_name=container_name,
            tail=tail,
        )
        return result if isinstance(result, str) else str(result)

    return [
        StructuredTool.from_function(
            func=commands.get_pods,
            name="ceph_pod_list",
            description=(
                "List pods in the openshift-storage namespace. "
                "Use this first to identify Ceph, Rook, and CSI pods "
                "available for troubleshooting."
            ),
        ),
        StructuredTool.from_function(
            func=commands.get_pods_wide,
            name="ceph_pod_list_wide",
            description=(
                "List pods in openshift-storage with additional details, "
                "including pod IP and node placement."
            ),
        ),
        StructuredTool.from_function(
            func=commands.get_pods_yaml,
            name="ceph_pod_list_yaml",
            description=(
                "Return YAML definitions for pods in openshift-storage. "
                "Use when detailed configuration across pods is required; "
                "prefer the single-pod tools when possible to reduce output."
            ),
        ),
        StructuredTool.from_function(
            func=commands.get_pod,
            name="ceph_pod_get_yaml",
            description=(
                "Get the YAML definition and current status for one pod in "
                "openshift-storage. Required input: pod_name."
            ),
        ),
        StructuredTool.from_function(
            func=commands.describe_pod,
            name="ceph_pod_describe",
            description=(
                "Describe one pod in openshift-storage, including events, "
                "conditions, container states, and diagnostic details. "
                "Required input: pod_name."
            ),
        ),
        StructuredTool.from_function(
            func=commands.get_pod_container_details,
            name="ceph_pod_container_details",
            description=(
                "List container details for a specified pod, including init, "
                "regular, and ephemeral containers, state, restart count, "
                "and waiting or termination reason. Call this before requesting "
                "container logs to discover valid container names. "
                "Required input: pod_name."
            ),
        ),
        StructuredTool.from_function(
            func=commands.get_pod_container_names,
            name="ceph_pod_container_names",
            description=(
                "Return the valid init, regular, and ephemeral container names "
                "for one pod in openshift-storage. Required input: pod_name."
            ),
        ),
        StructuredTool.from_function(
            func=get_container_logs,
            name="ceph_pod_container_logs",
            description=(
                "Get recent troubleshooting logs from one specific container "
                "in a pod in openshift-storage. Inputs: pod_name, the exact "
                "container_name returned by ceph_pod_container_details or "
                "ceph_pod_container_names, and optional tail (default 100). "
                "Recognized INFO-level lines are removed before the logs are "
                "returned; ERROR, WARN, FATAL, and unclassified lines are kept. "
                "Use this after identifying the correct pod and container."
            ),
        ),
    ]
