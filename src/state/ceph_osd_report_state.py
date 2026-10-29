from __future__ import annotations

from pydantic import BaseModel, Field


class OSDFinding(BaseModel):
    severity: str = Field(
        description="Finding severity: CRITICAL, WARNING, INFO, or HEALTHY."
    )

    category: str = Field(
        description="Category of the finding."
    )

    title: str = Field(
        description="Short title describing the finding."
    )

    description: str = Field(
        description="Detailed explanation of the finding."
    )

    evidence: list[str] = Field(
        default_factory=list,
        description="Evidence from the supplied OSD data."
    )

    impact: str = Field(
        default="",
        description="Potential operational impact."
    )

    recommendation: str = Field(
        default="",
        description="Recommended action."
    )


class OSDReport(BaseModel):
    osd_id: int = Field(
        description="Ceph OSD ID."
    )

    host: str = Field(
        default="",
        description="Host running the OSD."
    )

    status: str = Field(
        description="Overall assessment of this OSD."
    )

    assessment: str = Field(
        description="Detailed health assessment of the OSD."
    )

    findings: list[OSDFinding] = Field(
        default_factory=list,
        description="Findings identified for this OSD."
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommended actions for this OSD."
    )