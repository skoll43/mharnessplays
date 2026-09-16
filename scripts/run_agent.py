from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mharnessplays.hypervisor.runtime import RuntimeHypervisor


def main() -> None:
    hypervisor = RuntimeHypervisor()
    hypervisor.run_ticks(3)
    print("agent bootstrap run complete")


if __name__ == "__main__":
    main()
