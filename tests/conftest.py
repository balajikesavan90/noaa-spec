from __future__ import annotations

import sys
from pathlib import Path


# Make the repository's src-layout package importable for direct `pytest` runs.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
