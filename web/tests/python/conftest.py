from __future__ import annotations

import sys
from pathlib import Path


WEB_PYTHON_ROOT = Path(__file__).resolve().parents[2] / "python"
sys.dont_write_bytecode = True
sys.path.insert(0, str(WEB_PYTHON_ROOT))
