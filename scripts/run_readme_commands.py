from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"

# Commands that require infrastructure not available in standard CI.
SKIP_PREFIXES = (
    "docker ",
    "python3 -m venv",
    "source ",
    "python3 -m pip",
    "sha256sum",
)


def _should_skip(line: str) -> bool:
    stripped = line.strip()
    return any(stripped.startswith(prefix) for prefix in SKIP_PREFIXES)


def main() -> int:
    readme_text = README_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", readme_text, flags=re.DOTALL)
    if not blocks:
        raise SystemExit("No bash code blocks found in README.md")

    filtered_lines: list[str] = []
    for block in blocks:
        for line in block.strip().splitlines():
            if _should_skip(line):
                continue
            filtered_lines.append(line)

    if not filtered_lines:
        print("All README bash commands were skipped (infrastructure-dependent).")
        return 0

    command_script = "\n".join(filtered_lines)
    completed = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", command_script],
        cwd=PROJECT_ROOT,
        text=True,
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
