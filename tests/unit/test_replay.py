from __future__ import annotations

from pathlib import Path

from mharnessplays.emulator.gateway import EmulatorGateway
from mharnessplays.emulator.replay_io import ReplayRecorder
from mharnessplays.emulator.sources import ReplaySource


def test_record_and_replay_deterministically(tmp_path: Path) -> None:
    frames = tmp_path / "sample.frames"
    inputs = tmp_path / "sample.inputs"
    gateway = EmulatorGateway()
    recorder = ReplayRecorder(frames, inputs)

    expected_ids = []
    for _ in range(5):
        frame = gateway.step()
        expected_ids.append(frame.frame_id)
        recorder.record_frame(frame)
        recorder.record_input(0)
    recorder.close()

    replay = ReplaySource(frames)
    replayed_ids = []
    try:
        while True:
            replayed_ids.append(replay.next_frame().frame_id)
    except StopIteration:
        pass

    assert replayed_ids == expected_ids
