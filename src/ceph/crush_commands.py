from __future__ import annotations

from src.omc_client import OMCClient


class CephCrushCommands:
    """OMC commands for Ceph CRUSH diagnostics."""

    def __init__(self, client: OMCClient):
        self.client = client

    def class_ls(self) -> str:
        return self.client.run(["ceph", "osd", "crush", "class", "ls"])

    def dump(self) -> str:
        return self.client.run(["ceph", "osd", "crush", "dump"])

    def rule_dump(self) -> str:
        return self.client.run(["ceph", "osd", "crush", "rule", "dump"])

    def rule_ls(self) -> str:
        return self.client.run(["ceph", "osd", "crush", "rule", "ls"])

    def show_tunables(self) -> str:
        return self.client.run(["ceph", "osd", "crush", "show-tunables"])

    def weight_set_dump(self) -> str:
        return self.client.run(["ceph", "osd", "crush", "weight-set", "dump"])
