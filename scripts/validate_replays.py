from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mharnessplays.emulator.sources import ReplaySource


def validate_replay(path: Path) -> int:
    source = ReplaySource(path)
    count = 0
    try:
        while True:
            source.next_frame()
            count += 1
    except StopIteration:
        return count


def main() -> None:
    replay_path = Path("replays/replay_001.frames")
    if not replay_path.exists():
        print("missing replay_001.frames")
        return
    count = validate_replay(replay_path)
    print(f"validated frames={count}")


if __name__ == "__main__":
    main()
