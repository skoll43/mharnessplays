from __future__ import annotations

from mharnessplays.contracts import ActionProposal, EffectorReport, Frame
from mharnessplays.emulator.gateway import EmulatorGateway
from mharnessplays.perception.frame_differencer import FrameDifferencer

INPUT_MAP = {
    "NAVIGATE": 0b0001,
    "INTERACT": 0b0010,
    "OPEN_MENU": 0b0100,
    "CLOSE_MENU": 0b1000,
    "ADVANCE_TEXT": 0b0010,
    "WAIT": 0,
    "SAFE_PAUSE": 0,
}


class VisualServoingEffector:
    def __init__(self, gateway: EmulatorGateway) -> None:
        self._gateway = gateway
        self._differencer = FrameDifferencer()

    def execute(
        self,
        action: ActionProposal,
        expected_min_delta: float = 0.0,
        cancel: bool = False,
    ) -> EffectorReport:
        start_tick = self._gateway.get_tick()
        before = self._gateway.step()

        if cancel:
            after = before
            status = "INTERRUPTED"
            observed_delta = {"delta_ratio": 0.0}
            return EffectorReport(
                action_id=action.action_id,
                status=status,
                start_tick=start_tick,
                end_tick=self._gateway.get_tick(),
                expected_delta={"min_delta": expected_min_delta},
                observed_delta=observed_delta,
                failure_reason="cancellation token triggered",
            )

        self._gateway.send_input(INPUT_MAP.get(action.primitive, 0))
        after = self._gateway.step()
        delta = self._differencer.delta_ratio(before, after)

        if delta >= expected_min_delta:
            status = "SUCCESS"
            failure_reason = None
        else:
            status = "FAILED"
            failure_reason = "insufficient visual delta"

        return EffectorReport(
            action_id=action.action_id,
            status=status,
            start_tick=start_tick,
            end_tick=after.tick,
            expected_delta={"min_delta": expected_min_delta},
            observed_delta={"delta_ratio": delta},
            failure_reason=failure_reason,
        )


def make_dummy_frame(frame_id: int, tick: int, value: int) -> Frame:
    pixels = bytes([value] * 64)
    return Frame(
        frame_id=frame_id,
        tick=tick,
        timestamp_ms=tick * 16,
        width=8,
        height=8,
        pixels=pixels,
    )
