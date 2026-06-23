import importlib.util
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "specs_validate.py"
spec = importlib.util.spec_from_file_location("specs_validate", MODULE_PATH)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_specs_validate_compat_entry_loads():
    assert checker.main
    assert checker.build_parser


def test_specs_validate_all_cli_passes_on_current_repo(tmp_path):
    result = subprocess.run(
        [
            "python3",
            str(MODULE_PATH),
            "all",
            "--fail-on-diagnostics",
            "--root",
            str(PROJECT_ROOT),
            "--workspace-root",
            str(PROJECT_ROOT.parent),
            "--out",
            str(tmp_path / "index"),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "v2 active 规范诊断完成" in result.stdout
    assert "diagnostics: 0" in result.stdout


def test_specs_validate_all_cli_fails_when_doc_check_fails(tmp_path):
    bad_doc = tmp_path / "bad.md"
    bad_doc.write_text("# Bad\n\n## 三、错误章节\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            str(MODULE_PATH),
            "all",
            str(bad_doc),
            "--root",
            str(PROJECT_ROOT),
            "--workspace-root",
            str(PROJECT_ROOT.parent),
            "--specs-dir",
            "specs",
            "--out",
            str(tmp_path / "index"),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "03 文档基础规范检查失败" in result.stdout
    assert "中文大写编号" in result.stdout
