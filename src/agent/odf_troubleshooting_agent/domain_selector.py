# src/agent/odf_react/domain_selector.py

from __future__ import annotations


def select_domains(query: str) -> list[str]:
    text = query.lower()

    domains: set[str] = {
        "cluster_health"
    }

    if any(
        keyword in text
        for keyword in (
            "osd",
            "osds",
            "object storage daemon",
            "down osd",
            "out osd",
            "osd tree",
        )
    ):
        domains.add("osd")

    if any(
        keyword in text
        for keyword in (
            "pool",
            "pools",
            "pg",
            "autoscaler",
        )
    ):
        domains.add("pool")

    if any(
        keyword in text
        for keyword in (
            "mgr",
            "manager",
            "dashboard",
        )
    ):
        domains.add("mgr")

    if any(
        keyword in text
        for keyword in (
            "capacity",
            "full",
            "near full",
            "utilization",
            "usage",
        )
    ):
        domains.add("capacity")

    if any(
        keyword in text
        for keyword in (
            "crush",
            "placement",
            "device class",
        )
    ):
        domains.add("crush")

    if any(
        keyword in text
        for keyword in (
            "latency",
            "slow",
            "performance",
            "blocked",
        )
    ):
        domains.add("performance")

    return list(domains)