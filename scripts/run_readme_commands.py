from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"


def main() -> int:
    readme_text = README_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\n(.*?)```", readme_text, flags=re.DOTALL)
    if not blocks:
        raise SystemExit("No bash code blocks found in README.md")

    command_script = "\n\n".join(block.strip() for block in blocks if block.strip())
    completed = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", command_script],
        cwd=PROJECT_ROOT,
        text=True,
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
