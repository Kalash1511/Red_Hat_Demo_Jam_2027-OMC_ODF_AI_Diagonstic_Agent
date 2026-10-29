from __future__ import annotations

import json

from pydantic import BaseModel, Field

from src.state.ceph_osd_state import OSD


class OSDDiagnosticResult(BaseModel):
    """
    LLM response for a single OSD.
    """

    findings: list[str] = Field(
        default_factory=list,
        description="Findings identified from the OSD data."
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations based on the OSD data."
    )


class CephOSDDiagnostic:
    """
    Analyze one OSD at a time using the LLM.

    Only the selected OSD data is supplied to the LLM.
    """

    def __init__(self, llm):

        self.structured_llm = (
            llm.with_structured_output(
                OSDDiagnosticResult
            )
        )

    def analyze( self,osd: OSD,) -> OSDDiagnosticResult:
        """
        Analyze a single OSD.
        """

        osd_data = osd.model_dump(
            exclude={
                "findings",
                "recommendations",
            }
        )

        prompt = f"""
Analyze this Ceph OSD.

Identify any health or operational findings
supported by the supplied data.

Provide recommendations only when action is required.

Recommendation rules:
- Keep each recommendation and findings short and actionable.
- Each recommendation and findings should be one concise sentence.
- Do not provide explanations or long descriptions.
- Do not repeat the finding in the recommendation.
- Do not provide more than 2 recommendations for one OSD.
- If no action is required, return an empty recommendations list.

Use only the supplied OSD information.
Do not invent information.

OSD details:

{json.dumps(osd_data, indent=2)}
"""

        return self.structured_llm.invoke(
            prompt
        )