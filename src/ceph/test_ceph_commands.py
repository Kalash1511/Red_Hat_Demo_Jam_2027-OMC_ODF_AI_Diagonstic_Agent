from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

# Allow this script to be run directly from src/tools/.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.omc_client import OMCClient
from src.ceph.ceph_pod_commands import CephPodCommands


def create_commands() -> CephPodCommands:
    """Create the OMC client and Ceph pod command wrapper."""
    client = OMCClient(omc_path="omc")
    return CephPodCommands(client)


def _print_result(title: str, result: object) -> None:
    print(f"\n{'=' * 80}\n{title}\n{'=' * 80}")
    print(result)


def test_get_pods(commands: CephPodCommands) -> None:
    """List pods in the openshift-storage namespace."""
    _print_result("Pods in openshift-storage", commands.get_pods())


def test_get_pods_wide(commands: CephPodCommands) -> None:
    """List pods with additional placement and IP information."""
    _print_result("Pods (wide) in openshift-storage", commands.get_pods_wide())


def test_get_pods_yaml(commands: CephPodCommands) -> None:
    """Retrieve YAML for all pods in the namespace."""
    _print_result("Pods YAML in openshift-storage", commands.get_pods_yaml())


def test_get_pod(commands: CephPodCommands, pod_name: str) -> None:
    """Retrieve YAML details for one pod."""
    _print_result(f"Pod details: {pod_name}", commands.get_pod(pod_name))


def test_describe_pod(commands: CephPodCommands, pod_name: str) -> None:
    """Show pod status, conditions, events, and diagnostic details."""
    _print_result(f"Describe pod: {pod_name}", commands.describe_pod(pod_name))


def test_get_pod_container_names(commands: CephPodCommands, pod_name: str) -> None:
    """List init, regular, and ephemeral container names for a pod."""
    _print_result(
        f"Container names in pod: {pod_name}",
        commands.get_pod_container_names(pod_name),
    )


def test_get_pod_logs(
    commands: CephPodCommands,
    pod_name: str,
    container_name: str,
    tail: int = 100,
) -> None:
    """Get INFO-filtered troubleshooting logs from one specific container."""
    _print_result(
        f"Troubleshooting logs: {pod_name}/{container_name} (last {tail} lines; INFO filtered)",
        commands.get_pod_logs(pod_name, container_name=container_name, tail=tail),
    )


def test_info_log_filter(commands: CephPodCommands) -> None:
    """Smoke-test the INFO filter without querying the cluster."""
    sample_logs = "\n".join(
        [
            '2026-10-19T10:00:00Z level=info msg="normal operation"',
            '2026-10-19T10:00:01Z level=error msg="failed to reconcile resource"',
            '2026-10-19 10:00:02 INFO starting periodic check',
            '2026-10-19 10:00:03 ERROR failed to mount volume',
            'E1019 10:00:04.123456 1234 pod.go:42] container startup failed',
        ]
    )
    _print_result("Sample logs after INFO filtering", commands.filter_info_logs(sample_logs))


def main() -> None:
    """Run an individual Ceph pod command from an interactive menu."""
    commands = create_commands()

    menu: dict[str, tuple[str, Callable[[], None]]] = {
        "1": ("List pods", lambda: test_get_pods(commands)),
        "2": ("List pods (wide)", lambda: test_get_pods_wide(commands)),
        "3": ("Get all pod YAML", lambda: test_get_pods_yaml(commands)),
        "7": ("Test INFO-log filtering with sample data", lambda: test_info_log_filter(commands)),
    }

    while True:
        print("\nCeph Pod Commands Test")
        print("Namespace: openshift-storage")
        print("1. List pods")
        print("2. List pods (wide)")
        print("3. Get all pod YAML")
        print("4. Get a specific pod (YAML)")
        print("5. Describe a specific pod")
        print("6. Get troubleshooting logs from a specific container (INFO filtered)")
        print("7. Test INFO-log filtering with sample data")
        print("8. Get container names for a pod")
        print("0. Exit")

        choice = input("Select a command: ").strip()
        if choice == "0":
            print("Exiting.")
            break

        try:
            if choice in menu:
                menu[choice][1]()
            elif choice in {"4", "5", "6", "8"}:
                pod_name = input("Enter pod name: ").strip()
                if not pod_name:
                    print("Pod name cannot be empty.")
                    continue

                if choice == "4":
                    test_get_pod(commands, pod_name)
                elif choice == "5":
                    test_describe_pod(commands, pod_name)
                elif choice == "8":
                    test_get_pod_container_names(commands, pod_name)
                else:
                    # Show known container names first to help choose the exact name.
                    test_get_pod_container_names(commands, pod_name)
                    container_name = input("Enter container name for logs: ").strip()
                    if not container_name:
                        print("Container name cannot be empty.")
                        continue

                    tail_text = input("Number of recent lines [100]: ").strip()
                    tail = int(tail_text) if tail_text else 100
                    if tail < 1:
                        print("Number of log lines must be greater than zero.")
                        continue
                    test_get_pod_logs(
                        commands, pod_name, container_name=container_name, tail=tail
                    )
            else:
                print("Invalid selection. Choose 0-8.")
        except (ValueError, RuntimeError, OSError) as exc:
            print(f"Command failed: {exc}")
        except Exception as exc:  # Keep the runner usable if OMC raises another error.
            print(f"Unexpected error: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
