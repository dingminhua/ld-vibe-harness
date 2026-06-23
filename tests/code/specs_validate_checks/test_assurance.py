import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_assurance_script_fast_path_outputs_text():
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "assurance",
            str(PROJECT_ROOT / "specs" / "00-LDVH理念与价值标准.md"),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "规范保障要求检查通过" in result.stdout
