from __future__ import annotations

from pathlib import Path


def _coerce_scalar(raw: str):
    value = raw.strip()
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.replace(".", "", 1).isdigit():
        return float(value) if "." in value else int(value)
    return value


def load_yaml_like(path: Path) -> dict:
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]

    for line in path.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")

        while stack and indent <= stack[-1][0]:
            stack.pop()

        container = stack[-1][1]
        if value.strip() == "":
            new_obj: dict = {}
            container[key] = new_obj
            stack.append((indent, new_obj))
        else:
            container[key] = _coerce_scalar(value)

    return root


def main() -> None:
    config = load_yaml_like(Path("configs/default.yaml"))
    print("bootstrap config loaded", config.get("mode"))


if __name__ == "__main__":
    main()
