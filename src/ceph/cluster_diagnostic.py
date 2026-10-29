from __future__ import annotations

import json

from pydantic import BaseModel, Field

from src.state.ceph_osd_state import CephState


class ClusterDiagnosticResult(BaseModel):
    """
    Structured LLM response for the complete
    Ceph cluster health assessment.
    """

    assessment: str = Field(
        default="",
        description="Overall Ceph cluster health assessment.",
    )

    findings: list[str] = Field(
        default_factory=list,
        description="Important cluster-level findings.",
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Cluster-level recommendations.",
    )


class CephClusterDiagnostic:
    """
    Generates the overall Ceph cluster health assessment.

    The LLM receives:
        - Cluster-level information, including health and health_detail
        - Findings from every OSD
        - Recommendations from every OSD

    The full raw OSD metrics are not sent again because the
    per-OSD diagnostic results already summarize them.
    """

    def __init__(self, llm):
        self.structured_llm = llm.with_structured_output(
            ClusterDiagnosticResult
        )

    def analyze(
        self,
        state: CephState,
    ) -> ClusterDiagnosticResult:
        """
        Analyze the complete Ceph cluster using:
            - aggregated cluster data
            - Ceph health details
            - OSD diagnostics
        """

        # ----------------------------------------------------------
        # Cluster-level evidence
        # ----------------------------------------------------------

        # Do not send previous LLM-generated cluster results
        # back into the new analysis.
        cluster_data = state.cluster.model_dump(
            exclude={
                "findings",
                "recommendations",
                "assessment",
            }
        )

        # ----------------------------------------------------------
        # OSD diagnostic evidence
        # ----------------------------------------------------------

        osd_diagnostics = []

        for osd in state.osd_data.osds:
            osd_diagnostics.append(
                {
                    "osd_id": osd.id,
                    "host": osd.host,
                    "status": osd.status,
                    "findings": osd.findings,
                    "recommendations": osd.recommendations,
                }
            )

        # ----------------------------------------------------------
        # Prompt
        # ----------------------------------------------------------

        prompt = f"""
You are an expert Red Hat OpenShift and Ceph/ODF
storage diagnostic engineer.

Create the overall Ceph cluster health assessment
using BOTH:

1. Cluster-level Ceph information
2. Diagnostic results from all OSDs

The cluster-level Ceph health information is
authoritative and must be considered when producing
the final assessment.

IMPORTANT:
- Always consider the "health" field.
- Always consider the complete "health_detail" field.
- Do not classify the cluster as healthy merely
  because all OSDs are up and in.
- A cluster can have all OSDs operational and still
  be unhealthy because of PG, scrub, data consistency,
  replication, MON, MGR, or other Ceph health errors.
- Correlate cluster health errors with the available
  OSD diagnostic results.
- If cluster health reports an error, explicitly
  reflect that error in the assessment and findings.
- Do not ignore specific PGs, scrub errors,
  inconsistent PGs, or possible data damage reported
  in health_detail.

Use only the supplied evidence.

Do not invent:
- OSDs
- failures
- metrics
- capacity
- events
- conditions
- recommendations
- Ceph errors not present in the supplied data

Correlate the findings across the OSDs and cluster
health information.

Identify:
- Overall cluster health
- Important Ceph health errors
- Common or repeated OSD problems
- Important cluster-level risks
- OSD availability concerns
- Capacity or utilization concerns only when
  explicitly supported by the supplied data
- OSD imbalance concerns only when explicitly
  supported by the supplied data
- Important healthy conditions
- Operational risks

Do not blindly repeat every OSD finding.
Combine related findings where appropriate.

Assessment rules:
- The assessment must reflect the supplied Ceph
  cluster health state.
- Explain the main reason for the current health state.
- Include the most important cluster-level problem
  when one exists.
- Distinguish between OSD operational health and
  overall cluster health.
- Do not call the cluster healthy when the supplied
  Ceph health state indicates HEALTH_ERR.
- Do not claim data damage unless it is reported in
  the supplied evidence.

Finding rules:
- Include important cluster-level problems.
- Include the specific Ceph health errors reported
  in health_detail.
- Include relevant OSD correlation when supported.
- Keep findings concise.
- Do not provide more than 5 findings.

Recommendation rules:
- Provide only actionable recommendations.
- Keep each recommendation and finding short and concise.
- Each recommendation should be one sentence.
- Do not provide explanations or long descriptions.
- Do not simply repeat the finding in the recommendation.
- Do not provide more than 5 cluster-level recommendations.
- Recommendations must be supported by the supplied
  cluster or OSD evidence.
- If no action is required, return an empty list.

Produce:
1. Overall cluster assessment
2. Important cluster-level findings
3. Actionable cluster-level recommendations

============================================================
CLUSTER-LEVEL CEPH DATA
============================================================

{json.dumps(cluster_data, indent=2)}

============================================================
OSD DIAGNOSTIC RESULTS
============================================================

{json.dumps(osd_diagnostics, indent=2)}
"""

        return self.structured_llm.invoke(prompt)
