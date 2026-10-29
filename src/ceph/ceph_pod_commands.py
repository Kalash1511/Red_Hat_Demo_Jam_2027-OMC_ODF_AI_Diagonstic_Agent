from __future__ import annotations

import re
from typing import Any, Pattern

import yaml

from src.omc_client import OMCClient


class CephPodCommands:
    """OMC commands used for Ceph Pod diagnostics in openshift-storage."""

    NAMESPACE = "openshift-storage"

    # INFO-level formats commonly emitted by Kubernetes, Rook, and structured logs.
    _INFO_LOG_PATTERNS: tuple[Pattern[str], ...] = (
        re.compile(
            r"(?i)\b(?:level|severity)\s*[=:]\s*['\"]?info['\"]?(?=\s|[,;}\]]|$)"
        ),
        re.compile(r"(?i)['\"](?:level|severity)['\"]\s*:\s*['\"]info['\"]"),
        re.compile(r"(?i)^\s*(?:\[INFO\]|INFO)(?=\s|\||:|-|$)"),
        re.compile(
            r"(?i)^\s*\d{4}-\d{2}-\d{2}T\S+\s+(?:\[[^\]]+\]\s*)?\[?INFO\]?(?=\s|\||:|-|$)"
        ),
        re.compile(
            r"(?i)^\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\s+(?:-\s+)?\[?INFO\]?(?=\s|\||:|-|$)"
        ),
        re.compile(r"(?i)^.*\|\s*INFO\s*\|"),
        re.compile(r"^\s*I\d{4}\s+\d{2}:\d{2}:\d{2}\.\d+\b"),
    )

    def __init__(self, client: OMCClient):
        self.client = client

    def get_pods(self):
        """Get all pods in the openshift-storage namespace."""
        return self.client.run(["get", "pods", "-n", self.NAMESPACE])

    def get_pods_wide(self):
        """Get pod details, including node placement and IP addresses."""
        return self.client.run(["get", "pods", "-n", self.NAMESPACE, "-o", "wide"])

    def get_pods_yaml(self):
        """Get YAML definitions for all pods in the namespace."""
        return self.client.run(["get", "pods", "-n", self.NAMESPACE, "-o", "yaml"])

    def get_pod(self, pod_name: str):
        """Get YAML details for a specific pod."""
        self._validate_pod_name(pod_name)
        return self.client.run(
            ["get", "pod", pod_name, "-n", self.NAMESPACE, "-o", "yaml"]
        )

    def describe_pod(self, pod_name: str):
        """Get pod events, conditions, and diagnostic details."""
        self._validate_pod_name(pod_name)
        return self.client.run(["describe", "pod", pod_name, "-n", self.NAMESPACE])

    @staticmethod
    def _validate_pod_name(pod_name: str) -> None:
        if not pod_name or not pod_name.strip():
            raise ValueError("pod_name must not be empty")

    def get_pod_container_details(self, pod_name: str) -> list[dict[str, Any]]:
        """Return container names, types, states, and restart counts for a pod.

        Fetching and parsing the pod YAML is used instead of JSONPath because some
        OMC versions do not support the full set of kubectl output options.
        """
        self._validate_pod_name(pod_name)
        output = self.get_pod(pod_name)
        if not isinstance(output, str):
            raise RuntimeError(
                "Unable to parse pod details: OMCClient.run() did not return text."
            )

        try:
            pod_data = yaml.safe_load(output)
        except yaml.YAMLError as exc:
            raise RuntimeError(f"Unable to parse YAML for pod {pod_name}: {exc}") from exc

        if not isinstance(pod_data, dict):
            raise RuntimeError(
                f"OMC did not return a valid Pod YAML document for {pod_name}."
            )

        spec = pod_data.get("spec") or {}
        status = pod_data.get("status") or {}
        groups = (
            ("init", "initContainers", "initContainerStatuses"),
            ("regular", "containers", "containerStatuses"),
            ("ephemeral", "ephemeralContainers", "ephemeralContainerStatuses"),
        )

        details: list[dict[str, Any]] = []
        for container_type, spec_key, status_key in groups:
            declared = spec.get(spec_key) or []
            statuses = {
                item.get("name"): item
                for item in (status.get(status_key) or [])
                if isinstance(item, dict) and item.get("name")
            }
            for container in declared:
                if not isinstance(container, dict) or not container.get("name"):
                    continue
                name = str(container["name"])
                container_status = statuses.get(name, {})
                state = container_status.get("state") or {}
                if state.get("running") is not None:
                    state_name = "Running"
                    reason = ""
                elif state.get("waiting") is not None:
                    state_name = "Waiting"
                    reason = str((state.get("waiting") or {}).get("reason") or "")
                elif state.get("terminated") is not None:
                    state_name = "Terminated"
                    reason = str((state.get("terminated") or {}).get("reason") or "")
                else:
                    state_name = "Unknown"
                    reason = ""

                details.append(
                    {
                        "name": name,
                        "type": container_type,
                        "state": state_name,
                        "reason": reason,
                        "restart_count": int(container_status.get("restartCount") or 0),
                    }
                )

        if not details:
            raise RuntimeError(
                f"No init, regular, or ephemeral containers were found in pod {pod_name}."
            )
        return details

    def get_pod_container_names(self, pod_name: str) -> list[str]:
        """Get valid init, regular, and ephemeral container names for a pod."""
        return [item["name"] for item in self.get_pod_container_details(pod_name)]

    @classmethod
    def filter_info_logs(cls, log_text: str) -> str:
        """Remove recognizable INFO-level lines while retaining other diagnostics.

        Unclassified lines are retained to avoid accidentally discarding useful
        troubleshooting evidence.
        """
        retained_lines: list[str] = []
        for line in log_text.splitlines():
            if not any(pattern.search(line) for pattern in cls._INFO_LOG_PATTERNS):
                retained_lines.append(line)
        filtered = "\n".join(retained_lines).strip()
        if log_text.strip() and not filtered:
            return "No non-INFO log entries found; INFO-level entries were filtered out."
        return filtered

    def get_pod_logs(
        self,
        pod_name: str,
        container_name: str | None,
        tail: int = 100,
    ):
        """Get troubleshooting logs for one container, with INFO lines filtered."""
        self._validate_pod_name(pod_name)
        if container_name is None or not container_name.strip():
            raise ValueError("container_name is required and must not be empty")
        if tail < 1:
            raise ValueError("tail must be greater than zero")

        # OMC does not support kubectl's --prefix flag, so do not pass it.
        # Container identity is unambiguous because this command targets one -c.
        output = self.client.run(
            [
                "logs",
                pod_name,
                "-n",
                self.NAMESPACE,
                "-c",
                container_name,
                "--tail",
                str(tail),
            ]
        )
        if isinstance(output, str):
            return self.filter_info_logs(output)
        return output
