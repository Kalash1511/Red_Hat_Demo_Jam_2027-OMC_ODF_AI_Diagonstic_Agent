from __future__ import annotations

from src.omc_client import OMCClient


class CephMgrCommands:
    """OMC commands for Ceph manager diagnostics."""

    def __init__(self, client: OMCClient):
        self.client = client

    def dump(self) -> str:
        """Run `omc ceph mgr dump`."""
        return self.client.run(["ceph", "mgr", "dump"])

    def module_ls(self) -> str:
        """Run `omc ceph mgr module ls`."""
        return self.client.run(["ceph", "mgr", "module", "ls"])

    def services(self) -> str:
        """Run `omc ceph mgr services`."""
        return self.client.run(["ceph", "mgr", "services"])
