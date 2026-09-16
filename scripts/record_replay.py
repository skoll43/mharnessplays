from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mharnessplays.emulator.gateway import EmulatorGateway
from mharnessplays.emulator.replay_io import ReplayRecorder


def main() -> None:
    gateway = EmulatorGateway()
    recorder = ReplayRecorder(Path("replays/replay_001.frames"), Path("replays/replay_001.inputs"))
    for _ in range(10):
        frame = gateway.step()
        recorder.record_frame(frame)
        recorder.record_input(0)
    recorder.close()
    print("recorded replay_001")


if __name__ == "__main__":
    main()
