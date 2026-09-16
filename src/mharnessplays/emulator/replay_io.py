from __future__ import annotations

import base64
import json
from pathlib import Path

from mharnessplays.contracts import Frame


class ReplayRecorder:
    def __init__(self, frames_path: Path, inputs_path: Path) -> None:
        frames_path.parent.mkdir(parents=True, exist_ok=True)
        inputs_path.parent.mkdir(parents=True, exist_ok=True)
        self._frames = frames_path.open("w", encoding="utf-8")
        self._inputs = inputs_path.open("w", encoding="utf-8")

    def record_frame(self, frame: Frame) -> None:
        payload = {
            "frame_id": frame.frame_id,
            "tick": frame.tick,
            "timestamp_ms": frame.timestamp_ms,
            "width": frame.width,
            "height": frame.height,
            "pixels_b64": base64.b64encode(frame.pixels).decode("ascii"),
        }
        self._frames.write(json.dumps(payload) + "\n")

    def record_input(self, input_mask: int) -> None:
        self._inputs.write(json.dumps({"input_mask": int(input_mask)}) + "\n")

    def close(self) -> None:
        self._frames.close()
        self._inputs.close()
