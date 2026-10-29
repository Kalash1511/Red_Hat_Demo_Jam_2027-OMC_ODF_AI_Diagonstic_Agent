# src/agent/odf_react/query_routing.py

from __future__ import annotations


def select_command_focus(query: str) -> str | None:
    text = query.lower()

    if (
        "how many osd" in text
        or "how many osds" in text
        or "total osd" in text
        or "osd count" in text
    ):
        return "ceph_osd_stat"

    if "osd tree" in text:
        return "ceph_osd_tree"

    if (
        "osd utilization" in text
        or "osd usage" in text
    ):
        return "ceph_osd_df"

    if "health detail" in text:
        return "ceph_health_detail"

    return None