import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[3] / "code" / "specs_validate.py"
spec = importlib.util.spec_from_file_location("specs_validate", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write_md(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return path
