from __future__ import annotations

import hashlib

from mharnessplays.contracts import Frame


class TileHasher:
    def hash_frame(self, frame: Frame) -> str:
        digest = hashlib.sha256(frame.pixels).hexdigest()
        return digest
