import importlib.util
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / "code" / "bootstrap_code.py"
spec = importlib.util.spec_from_file_location("bootstrap_code", MODULE_PATH)
bootstrap_code = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap_code)


def test_bootstrap_code_compat_entry_loads():
    assert bootstrap_code.main
    assert bootstrap_code.build_parser
    assert bootstrap_code.INSTALL_PACKAGES == ("PyYAML", "pytest")


def test_bootstrap_code_check_only_passes_in_test_environment():
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--check-only"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "LDVH Code Python dependencies are available" in result.stdout
