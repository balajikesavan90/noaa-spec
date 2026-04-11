from __future__ import annotations

import re
import subprocess
import sys
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
SRC_PATH = PROJECT_ROOT / "src"

# Commands that require infrastructure not available in standard CI.
SKIP_PREFIXES = (
    "docker ",
    "sudo apt ",
    "python3 -m venv",
    "source ",
    "python -m pip",
    "python3 -m pip",
    "python3 examples/download_and_clean_station.py",
    "--station ",
    "--start-year ",
    "--end-year ",
    "--output-dir ",
    "sha256sum",
)


def _normalize_line(line: str) -> str:
    quoted = line.lstrip()
    if not quoted.startswith(">"):
        return line.rstrip()

    while quoted.startswith(">"):
        quoted = quoted[1:]
        if quoted.startswith(" "):
            quoted = quoted[1:]
        quoted = quoted.lstrip("\t")
    return quoted.rstrip()


def _should_skip(line: str) -> bool:
    stripped = _normalize_line(line).strip()
    return any(stripped.startswith(prefix) for prefix in SKIP_PREFIXES)


def main() -> int:
    readme_text = README_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", readme_text, flags=re.DOTALL)
    if not blocks:
        raise SystemExit("No bash code blocks found in README.md")

    filtered_lines: list[str] = []
    for block in blocks:
        for line in block.strip().splitlines():
            normalized_line = _normalize_line(line)
            if not normalized_line.strip():
                continue
            if _should_skip(normalized_line):
                continue
            filtered_lines.append(normalized_line)

    if not filtered_lines:
        print("All README bash commands were skipped (infrastructure-dependent).")
        return 0

    command_script = "\n".join(filtered_lines)
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{SRC_PATH}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(SRC_PATH)
    )
    completed = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", command_script],
        cwd=PROJECT_ROOT,
        text=True,
        env=env,
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
