from __future__ import annotations

from src.ceph.crush_commands import CephCrushCommands
from src.ceph.health_commands import CephHealthCommands
from src.ceph.mgr_commands import CephMgrCommands
from src.ceph.osd_commands import CephOSDCommands
from src.ceph.pool_commands import CephPoolCommands
from src.omc_client import OMCClient
from src.ceph.ceph_pod_commands import CephPodCommands
from src.tools.ceph_tools.command_definition import CommandDefinition
from src.tools.ceph_tools.command_registry import OMCCommandRegistry


def build_ceph_command_registry(client: OMCClient) -> OMCCommandRegistry:
    """Build the allow-listed Ceph and Ceph pod OMC command registry."""
    osd = CephOSDCommands(client)
    health = CephHealthCommands(client)
    pool = CephPoolCommands(client)
    mgr = CephMgrCommands(client)
    crush = CephCrushCommands(client)
    pods = CephPodCommands(client)

    # Keep container_name required for registry consumers and LLM tool schemas.
    def get_container_logs(
        pod_name: str,
        container_name: str,
        tail: int = 100,
    ):
        """Return filtered troubleshooting logs from one named container."""
        return pods.get_pod_logs(
            pod_name=pod_name,
            container_name=container_name,
            tail=tail,
        )

    commands = [
        CommandDefinition(
            name="ceph_health_detail",
            description="Get detailed Ceph cluster health information.",
            domains=frozenset({"cluster_health", "osd", "pool", "capacity"}),
            execute=health.health_detail,
            when_to_use="Start here when a Ceph or ODF health problem is reported or the root cause is unclear.",
            evidence_type="cluster_health",
            priority=10,
        ),
        CommandDefinition(
            name="ceph_osd_stat",
            description="Get total, up and in Ceph OSD counts.",
            domains=frozenset({"cluster_health", "osd", "capacity"}),
            execute=osd.osd_stat,
            when_to_use="Use to confirm OSD availability and cluster-level OSD counts.",
            evidence_type="osd_status_summary",
            priority=20,
        ),
        CommandDefinition(
            name="ceph_osd_tree",
            description="Get the Ceph OSD tree, hierarchy, host placement, and UP/DOWN and IN/OUT state.",
            domains=frozenset({"cluster_health", "osd", "crush"}),
            execute=osd.osd_tree,
            when_to_use="Use when an OSD is DOWN/OUT or placement/topology needs investigation.",
            evidence_type="osd_topology",
            priority=20,
        ),
        CommandDefinition(
            name="ceph_osd_df",
            description="Get OSD capacity, utilization, PG distribution, and utilization variance.",
            domains=frozenset({"osd", "capacity", "performance", "cluster_health"}),
            execute=osd.osd_df,
            when_to_use="Use for capacity, imbalance, utilization, or PG distribution investigations.",
            evidence_type="osd_capacity",
            priority=20,
        ),
        CommandDefinition(
            name="ceph_osd_df_tree",
            description="Get OSD utilization in the CRUSH tree view.",
            domains=frozenset({"osd", "capacity", "crush"}),
            execute=osd.df_tree,
            when_to_use="Use when correlating utilization with CRUSH placement.",
            evidence_type="osd_capacity_tree",
        ),
        CommandDefinition(
            name="ceph_osd_dump",
            description="Get the Ceph OSD map dump.",
            domains=frozenset({"osd", "cluster_health"}),
            execute=osd.dump,
            when_to_use="Use when deeper OSD-map state is required.",
            evidence_type="osd_map",
        ),
        CommandDefinition(
            name="ceph_osd_perf",
            description="Get Ceph OSD performance statistics.",
            domains=frozenset({"osd", "performance", "cluster_health"}),
            execute=osd.perf,
            when_to_use="Use when investigating OSD latency or performance concerns.",
            evidence_type="osd_performance",
        ),
        CommandDefinition(
            name="ceph_osd_utilization",
            description="Get Ceph OSD utilization information.",
            domains=frozenset({"osd", "capacity", "performance"}),
            execute=osd.utilization,
            when_to_use="Use when utilization imbalance is suspected.",
            evidence_type="osd_utilization",
        ),
        CommandDefinition(
            name="ceph_osd_blocked_by",
            description="Get OSD operations blocked by other operations.",
            domains=frozenset({"osd", "performance", "cluster_health"}),
            execute=osd.blocked_by,
            when_to_use="Use when OSD operations appear blocked or stalled.",
            evidence_type="osd_blocked_operations",
        ),
        CommandDefinition(
            name="ceph_osd_lspools",
            description="List Ceph OSD pools.",
            domains=frozenset({"osd", "pool"}),
            execute=osd.lspools,
            when_to_use="Use when correlating OSD information with pools.",
            evidence_type="pool_list",
        ),
        CommandDefinition(
            name="ceph_osd_getmaxosd",
            description="Get the maximum OSD ID known by Ceph.",
            domains=frozenset({"osd"}),
            execute=osd.getmaxosd,
            when_to_use="Use when OSD ID allocation/state needs checking.",
            evidence_type="osd_id_state",
        ),
        CommandDefinition(
            name="ceph_osd_numa_status",
            description="Get Ceph OSD NUMA status.",
            domains=frozenset({"osd", "performance"}),
            execute=osd.numa_status,
            when_to_use="Use for NUMA-related OSD performance investigations.",
            evidence_type="osd_numa",
        ),
        CommandDefinition(
            name="ceph_osd_pool_autoscale_status",
            description="Get Ceph pool autoscaler status.",
            domains=frozenset({"pool", "capacity", "cluster_health"}),
            execute=pool.autoscale_status,
            when_to_use="Use when pool PG autoscaling or sizing is suspected.",
            evidence_type="pool_autoscaler",
        ),
        CommandDefinition(
            name="ceph_osd_pool_ls_detail",
            description="Get detailed Ceph pool configuration.",
            domains=frozenset({"pool", "capacity", "cluster_health"}),
            execute=pool.ls_detail,
            when_to_use="Use when investigating pool configuration or capacity.",
            evidence_type="pool_details",
        ),
        CommandDefinition(
            name="ceph_mgr_dump",
            description="Get the Ceph manager map and state.",
            domains=frozenset({"mgr", "cluster_health", "performance"}),
            execute=mgr.dump,
            when_to_use="Use when MGR availability or state is relevant.",
            evidence_type="mgr_state",
        ),
        CommandDefinition(
            name="ceph_mgr_module_ls",
            description="List Ceph manager modules and their state.",
            domains=frozenset({"mgr", "cluster_health"}),
            execute=mgr.module_ls,
            when_to_use="Use when an MGR module problem is suspected.",
            evidence_type="mgr_modules",
        ),
        CommandDefinition(
            name="ceph_mgr_services",
            description="Get Ceph manager service endpoints.",
            domains=frozenset({"mgr", "cluster_health"}),
            execute=mgr.services,
            when_to_use="Use when MGR service availability or connectivity matters.",
            evidence_type="mgr_services",
        ),
        CommandDefinition(
            name="ceph_osd_crush_class_ls",
            description="List Ceph CRUSH device classes.",
            domains=frozenset({"crush", "osd", "capacity"}),
            execute=crush.class_ls,
            when_to_use="Use when device-class placement needs investigation.",
            evidence_type="crush_classes",
        ),
        CommandDefinition(
            name="ceph_osd_crush_dump",
            description="Get the Ceph CRUSH map dump.",
            domains=frozenset({"crush", "osd"}),
            execute=crush.dump,
            when_to_use="Use when placement hierarchy or rules need deeper investigation.",
            evidence_type="crush_map",
        ),
        CommandDefinition(
            name="ceph_osd_crush_rule_dump",
            description="Get Ceph CRUSH rule definitions.",
            domains=frozenset({"crush", "osd", "pool"}),
            execute=crush.rule_dump,
            when_to_use="Use when pool or OSD placement behavior needs explanation.",
            evidence_type="crush_rules",
        ),
        CommandDefinition(
            name="ceph_osd_crush_rule_ls",
            description="List Ceph CRUSH rules.",
            domains=frozenset({"crush", "pool", "osd"}),
            execute=crush.rule_ls,
            when_to_use="Use when identifying the active CRUSH rules.",
            evidence_type="crush_rule_list",
        ),
        CommandDefinition(
            name="ceph_osd_crush_show_tunables",
            description="Get Ceph CRUSH tunables.",
            domains=frozenset({"crush", "performance", "cluster_health"}),
            execute=crush.show_tunables,
            when_to_use="Use when CRUSH tuning or compatibility is relevant.",
            evidence_type="crush_tunables",
        ),
        CommandDefinition(
            name="ceph_osd_crush_weight_set_dump",
            description="Get Ceph CRUSH weight-set information.",
            domains=frozenset({"crush", "capacity", "osd"}),
            execute=crush.weight_set_dump,
            when_to_use="Use when CRUSH weight distribution needs inspection.",
            evidence_type="crush_weights",
        ),
        # Ceph pod commands are registered in this same registry.
        CommandDefinition(
            name="ceph_pod_list",
            description=(
                "List pods in the openshift-storage namespace, including Ceph, "
                "Rook, and CSI components."
            ),
            domains=frozenset({"pod", "container", "cluster_health", "odf"}),
            execute=pods.get_pods,
            when_to_use=(
                "Start here to discover candidate Ceph/ODF pods when the affected "
                "pod name is unknown or the problem scope is unclear."
            ),
            evidence_type="pod_list",
            priority=10,
        ),
        CommandDefinition(
            name="ceph_pod_list_wide",
            description=(
                "List openshift-storage pods with details such as pod IP addresses "
                "and node placement."
            ),
            domains=frozenset({"pod", "node", "network", "cluster_health", "odf"}),
            execute=pods.get_pods_wide,
            when_to_use=(
                "Use to correlate a pod with its node or IP address, or to investigate "
                "pod placement and connectivity."
            ),
            evidence_type="pod_placement",
            priority=20,
        ),
        CommandDefinition(
            name="ceph_pod_list_yaml",
            description=(
                "Get YAML definitions for pods in openshift-storage. This may return "
                "a large amount of configuration and status data."
            ),
            domains=frozenset({"pod", "container", "configuration", "cluster_health", "odf"}),
            execute=pods.get_pods_yaml,
            when_to_use=(
                "Use when configuration across multiple pods must be compared. "
                "Prefer a single-pod YAML query when the target is known."
            ),
            evidence_type="pods_yaml",
            priority=60,
        ),
        CommandDefinition(
            name="ceph_pod_get_yaml",
            description=(
                "Get the YAML definition and current status for one pod in "
                "openshift-storage. Requires pod_name."
            ),
            domains=frozenset({"pod", "container", "configuration", "cluster_health", "odf"}),
            execute=pods.get_pod,
            when_to_use=(
                "Use after identifying the affected pod to inspect its specification, "
                "declared containers, scheduling details, and current status."
            ),
            evidence_type="pod_yaml",
            priority=20,
        ),
        CommandDefinition(
            name="ceph_pod_describe",
            description=(
                "Describe one pod in openshift-storage, including conditions, events, "
                "container state, and diagnostic details. Requires pod_name."
            ),
            domains=frozenset({"pod", "container", "events", "cluster_health", "odf"}),
            execute=pods.describe_pod,
            when_to_use=(
                "Use when a pod is Pending, not Ready, restarting, failing to start, "
                "or when Kubernetes events and status reasons are needed."
            ),
            evidence_type="pod_diagnostics",
            priority=15,
        ),
        CommandDefinition(
            name="ceph_pod_container_details",
            description=(
                "Get container names, container type, state, restart count, and "
                "waiting or termination reason for one pod. Requires pod_name."
            ),
            domains=frozenset({"pod", "container", "cluster_health", "odf"}),
            execute=pods.get_pod_container_details,
            when_to_use=(
                "Use before requesting logs to identify valid container names and "
                "find containers that are waiting, terminated, or restarting."
            ),
            evidence_type="pod_container_status",
            priority=15,
        ),
        CommandDefinition(
            name="ceph_pod_container_names",
            description=(
                "List init, regular, and ephemeral container names for one pod in "
                "openshift-storage. Requires pod_name."
            ),
            domains=frozenset({"pod", "container", "cluster_health", "odf"}),
            execute=pods.get_pod_container_names,
            when_to_use=(
                "Use when only valid container names are needed. For container state "
                "and restart information, prefer ceph_pod_container_details."
            ),
            evidence_type="pod_container_names",
            priority=25,
        ),
        CommandDefinition(
            name="ceph_pod_container_logs",
            description=(
                "Get recent troubleshooting logs from one specific container in a pod "
                "in openshift-storage. Requires pod_name and container_name; tail "
                "defaults to 100 lines. Recognized INFO-level lines are filtered out, "
                "while warning, error, fatal, and unclassified lines are retained."
            ),
            domains=frozenset({"pod", "container", "logs", "troubleshooting", "cluster_health", "odf"}),
            execute=get_container_logs,
            when_to_use=(
                "Use after identifying the affected pod and exact container name. "
                "Inspect container details first when the container name is unknown. "
                "Treat filtered logs as evidence rather than the sole basis for a diagnosis."
            ),
            evidence_type="pod_container_logs",
            priority=20,
        ),
    ]

    return OMCCommandRegistry(commands)
