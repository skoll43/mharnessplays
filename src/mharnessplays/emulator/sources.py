from __future__ import annotations

import base64
import json
from abc import ABC, abstractmethod
from pathlib import Path

from mharnessplays.contracts import Frame


class FrameSource(ABC):
    @abstractmethod
    def next_frame(self) -> Frame:
        raise NotImplementedError

    @abstractmethod
    def frame_id(self) -> int:
        raise NotImplementedError


class ReplaySource(FrameSource):
    def __init__(self, replay_path: Path) -> None:
        self._entries = replay_path.read_text().splitlines()
        self._index = 0
        self._frame_id = -1

    def next_frame(self) -> Frame:
        if self._index >= len(self._entries):
            raise StopIteration
        entry = json.loads(self._entries[self._index])
        self._index += 1
        pixels = base64.b64decode(entry["pixels_b64"])
        frame = Frame(
            frame_id=int(entry["frame_id"]),
            tick=int(entry["tick"]),
            timestamp_ms=int(entry["timestamp_ms"]),
            width=int(entry["width"]),
            height=int(entry["height"]),
            pixels=pixels,
        )
        self._frame_id = frame.frame_id
        return frame

    def frame_id(self) -> int:
        return self._frame_id
