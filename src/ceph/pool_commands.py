from __future__ import annotations

from src.omc_client import OMCClient


class CephPoolCommands:
    """OMC commands for Ceph pool diagnostics."""

    def __init__(self, client: OMCClient):
        self.client = client

    def autoscale_status(self) -> str:
        """Run `omc ceph osd pool autoscale-status`."""
        return self.client.run(["ceph", "osd", "pool", "autoscale-status"])

    def ls_detail(self) -> str:
        """Run `omc ceph osd pool ls detail`."""
        return self.client.run(["ceph", "osd", "pool", "ls", "detail"])
