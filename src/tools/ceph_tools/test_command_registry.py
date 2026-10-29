from __future__ import annotations

from inspect import signature
from unittest.mock import Mock

from src.omc_client import OMCClient
from src.tools.ceph_tools.ceph_tool_registry import build_ceph_command_registry


EXPECTED_POD_COMMANDS = (
    "ceph_pod_list",
    "ceph_pod_list_wide",
    "ceph_pod_list_yaml",
    "ceph_pod_get_yaml",
    "ceph_pod_describe",
    "ceph_pod_container_details",
    "ceph_pod_container_names",
    "ceph_pod_container_logs",
)

REQUIRED_ARGUMENTS = {
    "ceph_pod_get_yaml": {"pod_name"},
    "ceph_pod_describe": {"pod_name"},
    "ceph_pod_container_details": {"pod_name"},
    "ceph_pod_container_names": {"pod_name"},
    "ceph_pod_container_logs": {"pod_name", "container_name"},
}


def main() -> None:
    # Mock the OMC client so registry tests do not execute cluster commands.
    client = Mock(spec=OMCClient)
    registry = build_ceph_command_registry(client)

    registered_names = set(registry.names())

    print("Total registered Ceph commands:", len(registry.all()))
    print("Has health detail:", "ceph_health_detail" in registered_names)

    health = registry.get("ceph_health_detail")
    print("Health domains:", sorted(health.domains))

    assert "cluster_health" in health.domains
    assert "osd" in health.domains
    assert "pool" in health.domains
    assert "capacity" in health.domains

    print("\nOSD domain commands:")
    for command in registry.for_domain("osd"):
        print("  -", command.tool_name)

    print("\nPod domain commands:")
    for command in registry.for_domain("pod"):
        print("  -", command.tool_name)

    missing_commands = set(EXPECTED_POD_COMMANDS) - registered_names
    assert not missing_commands, (
        "Missing expected pod commands: " + ", ".join(sorted(missing_commands))
    )

    # Ensure parameterized commands expose the arguments required by callers.
    print("\nParameterized pod command signatures:")
    for command_name, expected_args in REQUIRED_ARGUMENTS.items():
        command = registry.get(command_name)
        actual_args = set(signature(command.execute).parameters)
        missing_args = expected_args - actual_args
        assert not missing_args, (
            f"{command_name} is missing parameters: "
            f"{', '.join(sorted(missing_args))}"
        )
        print(f"  - {command_name}{signature(command.execute)}")

    # Check that the log command requires a specific container name.
    log_signature = signature(registry.get("ceph_pod_container_logs").execute)
    container_parameter = log_signature.parameters["container_name"]
    assert container_parameter.default is container_parameter.empty, (
        "container_name must be required for ceph_pod_container_logs"
    )

    print("\nCommand registry validation passed.")
    print("Pod command registration and required arguments validated.")
    print("No OMC commands were executed; the OMC client was mocked.")


if __name__ == "__main__":
    main()
