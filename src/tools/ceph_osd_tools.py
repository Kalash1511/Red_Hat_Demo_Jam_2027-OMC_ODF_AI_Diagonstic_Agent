from __future__ import annotations

from langchain_core.tools import StructuredTool

from src.ceph.osd_commands import CephOSDCommands
from src.omc_client import OMCClient


def create_ceph_tools(
    client: OMCClient,
) -> list[StructuredTool]:
    """
    Create LangChain tools for Ceph diagnostics.
    """

    commands = CephOSDCommands(client)

    return [
        StructuredTool.from_function(
            func=commands.health_detail,
            name="ceph_health_detail",
            description=(
                "Run 'omc ceph health detail'. "
                "Use this to determine the overall "
                "Ceph cluster health and identify "
                "health warnings or errors."
            ),
        ),

        StructuredTool.from_function(
            func=commands.osd_stat,
            name="ceph_osd_stat",
            description=(
                "Run 'omc ceph osd stat'. "
                "Returns total, up and in OSD counts "
                "for the Ceph cluster."
            ),
        ),

        StructuredTool.from_function(
            func=commands.osd_tree,
            name="ceph_osd_tree",
            description=(
                "Run 'omc ceph osd tree'. "
                "Returns the Ceph CRUSH hierarchy "
                "and maps OSDs to their hosts."
            ),
        ),

        StructuredTool.from_function(
            func=commands.osd_df,
            name="ceph_osd_df",
            description=(
                "Run 'omc ceph osd df'. "
                "Returns OSD capacity, utilization, "
                "variance, PG distribution and status "
                "for all OSDs."
            ),
        ),
    ]