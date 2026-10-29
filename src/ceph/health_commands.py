from __future__ import annotations

from src.omc_client import OMCClient


class CephHealthCommands:
    """OMC commands for Ceph cluster health diagnostics."""

    def __init__(self, client: OMCClient):
        self.client = client

    def health_detail(self) -> str:
        """Run `omc ceph health detail`."""
        return self.client.run(["ceph", "health", "detail"])
