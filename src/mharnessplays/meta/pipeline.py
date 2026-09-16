from __future__ import annotations

from pathlib import Path

from mharnessplays.contracts import IncidentPacket, PatchProposal


class ProposalPipeline:
    def __init__(self, proposals_dir: Path, live_patch_mode: bool = False) -> None:
        self._proposals_dir = proposals_dir
        self._proposals_dir.mkdir(parents=True, exist_ok=True)
        self._live_patch_mode = live_patch_mode

    def propose(self, incident: IncidentPacket) -> PatchProposal:
        proposal = PatchProposal(
            proposal_id=f"proposal-{incident.incident_id}",
            incident_id=incident.incident_id,
            risk_level="medium",
            target="calibration",
            type="calibration",
            diff_ref="none",
            tests_required=["unit", "replay", "shadow"],
            rollback_ref="rollback-artifact",
            status="queued",
        )
        path = self._proposals_dir / f"{proposal.proposal_id}.txt"
        path.write_text(
            "\n".join(
                [
                    f"proposal_id={proposal.proposal_id}",
                    f"incident_id={proposal.incident_id}",
                    "promotable=false",
                    "reason=bootstrap proposal-only mode",
                ]
            )
        )
        return proposal

    def apply_live_patch(self, proposal: PatchProposal) -> None:
        if not self._live_patch_mode:
            raise PermissionError("live patching disabled in bootstrap mode")
        raise NotImplementedError("live patching is not part of bootstrap")
