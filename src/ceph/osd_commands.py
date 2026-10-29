from __future__ import annotations

from src.omc_client import OMCClient


class CephOSDCommands:
    """
    OMC commands used for Ceph OSD diagnostics.
    """

    def __init__(self, client: OMCClient):
        self.client = client

    def health_detail(self) -> str:
        """
        Run:

            omc ceph health detail
        """

        return self.client.run(
            ["ceph", "health", "detail"]
        )

    def osd_stat(self) -> str:
        """
        Run:

            omc ceph osd stat
        """

        return self.client.run(
            ["ceph", "osd", "stat"]
        )

    def osd_tree(self) -> str:
        """
        Run:

            omc ceph osd tree
        """

        return self.client.run(
            ["ceph", "osd", "tree"]
        )

    def osd_df(self) -> str:
        """
        Run:

            omc ceph osd df
        """

        return self.client.run(
            ["ceph", "osd", "df"]
        )
    def blocked_by(self) -> str:
        """Run `omc ceph osd blocked-by`."""
        return self.client.run(["ceph", "osd", "blocked-by"])

    def df_tree(self) -> str:
        """Run `omc ceph osd df tree`."""
        return self.client.run(["ceph", "osd", "df", "tree"])

    def dump(self) -> str:
        """Run `omc ceph osd dump`."""
        return self.client.run(["ceph", "osd", "dump"])

    def getmaxosd(self) -> str:
        """Run `omc ceph osd getmaxosd`."""
        return self.client.run(["ceph", "osd", "getmaxosd"])

    def lspools(self) -> str:
        """Run `omc ceph osd lspools`."""
        return self.client.run(["ceph", "osd", "lspools"])

    def numa_status(self) -> str:
        """Run `omc ceph osd numa-status`."""
        return self.client.run(["ceph", "osd", "numa-status"])

    def perf(self) -> str:
        """Run `omc ceph osd perf`."""
        return self.client.run(["ceph", "osd", "perf"])

    def utilization(self) -> str:
        """Run `omc ceph osd utilization`."""
        return self.client.run(["ceph", "osd", "utilization"])
