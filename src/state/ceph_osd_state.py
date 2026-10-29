from __future__ import annotations

from pydantic import BaseModel, Field


class OSD(BaseModel):
    """
    Structured information for a single Ceph OSD.
    """

    id: int = Field(
        default=-1,
        description="Ceph OSD ID."
    )

    host: str = Field(
        default="",
        description="Host on which the OSD is running."
    )

    device_class: str = Field(
        default="",
        description="OSD device class, for example ssd or hdd."
    )

    weight: float = Field(
        default=0.0,
        description="CRUSH weight of the OSD."
    )

    reweight: float = Field(
        default=0.0,
        description="Current OSD reweight value."
    )

    size: str = Field(
        default="",
        description="Total OSD capacity."
    )

    raw_use: str = Field(
        default="",
        description="Raw space used by the OSD."
    )

    data: str = Field(
        default="",
        description="Data usage of the OSD."
    )

    omap: str = Field(
        default="",
        description="OMAP usage of the OSD."
    )

    meta: str = Field(
        default="",
        description="Metadata usage of the OSD."
    )

    avail: str = Field(
        default="",
        description="Available OSD capacity."
    )

    percent_used: float = Field(
        default=0.0,
        description="Percentage of OSD capacity used."
    )

    variance: float = Field(
        default=0.0,
        description="OSD utilization variance."
    )

    pgs: int = Field(
        default=0,
        description="Number of placement groups assigned to the OSD."
    )

    status: str = Field(
        default="",
        description="OSD status."
    )

    findings: list[str] = Field(
        default_factory=list,
        description="Diagnostic findings identified for this OSD."
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations identified for this OSD."
    )


class OSDData(BaseModel):
    """
    Aggregated OSD information for the Ceph cluster.
    """

    osds: list[OSD] = Field(
        default_factory=list,
        description="All OSDs in the Ceph cluster."
    )

    total_osds: int = Field(
        default=0,
        description="Total number of OSDs."
    )

    up_osds: int = Field(
        default=0,
        description="Number of OSDs that are up."
    )

    in_osds: int = Field(
        default=0,
        description="Number of OSDs that are in."
    )

    down_osds: int = Field(
        default=0,
        description="Number of OSDs that are down."
    )

    out_osds: int = Field(
        default=0,
        description="Number of OSDs that are out."
    )


class CephClusterData(BaseModel):
    health: str = Field(
        default="",
        description="Ceph health status."
    )

    health_detail: str = Field(
        default="",
        description="Detailed Ceph health output."
    )

    total_osds: int = Field(
        default=0,
        description="Total OSD count."
    )

    up_osds: int = Field(
        default=0,
        description="Number of OSDs that are up."
    )

    in_osds: int = Field(
        default=0,
        description="Number of OSDs that are in."
    )

    total_capacity: str = Field(
        default="",
        description="Total raw Ceph capacity."
    )

    total_used: str = Field(
        default="",
        description="Total raw capacity used."
    )

    total_available: str = Field(
        default="",
        description="Total available raw capacity."
    )

    overall_percent_used: float = Field(
        default=0.0,
        description="Overall raw capacity utilization."
    )

    min_variance: float = Field(
        default=0.0,
        description="Minimum OSD utilization variance."
    )

    max_variance: float = Field(
        default=0.0,
        description="Maximum OSD utilization variance."
    )

    stddev: float = Field(
        default=0.0,
        description="Standard deviation of OSD utilization."
    )

    findings: list[str] = Field(
        default_factory=list,
        description="Cluster-level diagnostic findings."
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Cluster-level recommendations."
    )

    assessment: str = Field(
        default="",
        description="Overall Ceph cluster health assessment."
    )

class CephState(BaseModel):
    """
    State used by the Ceph/ODF report workflow.
    """

    must_gather_path: str = Field(
        default="",
        description="Path to the must-gather."
    )

    cluster: CephClusterData = Field(
        default_factory=CephClusterData
    )

    osd_data: OSDData = Field(
        default_factory=OSDData
    )

    validation_errors: list[str] = Field(
        default_factory=list
    )

    cluster_validated: bool = Field(
        default=False
    )

    osds_validated: bool = Field(
        default=False
    )