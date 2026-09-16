# mharnessplays

Bootstrap implementation for a **pixel-only**, dual-loop autonomous Game Boy agent.

## Guarantees in bootstrap mode

- No RAM reads for live inference.
- No direct LLM-to-input path.
- No live hot patching.
- Deterministic replay support.
- Action validation and transition input blocking.

## Quickstart

```bash
pytest
ruff check .
python scripts/validate_replays.py
```
