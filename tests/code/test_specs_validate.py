import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "specs_validate.py"
spec = importlib.util.spec_from_file_location("specs_validate", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_specs_validate_compat_entry_loads():
    assert checker.main
    assert checker.build_parser
