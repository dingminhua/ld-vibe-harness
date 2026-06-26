import importlib.util
import os
import stat
import subprocess
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "code" / "install_git_hooks.py"
spec = importlib.util.spec_from_file_location("install_git_hooks", MODULE_PATH)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def init_repo(path: Path) -> Path:
    path.mkdir()
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    return path


def test_render_commit_msg_hook_calls_dispatcher():
    root = Path("/tmp/ldvh")
    repo = Path("/tmp/repo")

    content = installer.render_commit_msg_hook(root, repo)

    assert installer.MARKER in content
    assert "code/hook_dispatch.py" in content
    assert "run git.commit-msg" in content
    assert '--cwd "$REPO_ROOT"' in content
    assert '--message-file "$MSG_FILE"' in content


def test_install_commit_msg_hook_writes_executable_hook(tmp_path):
    repo = init_repo(tmp_path / "repo")
    ldvh_root = tmp_path / "ldvh"
    ldvh_root.mkdir()

    target = installer.install_commit_msg_hook(repo, ldvh_root)

    assert target.name == "commit-msg"
    assert installer.MARKER in target.read_text(encoding="utf-8")
    assert os.access(target, os.X_OK)


def test_install_refuses_foreign_hook_without_force(tmp_path):
    repo = init_repo(tmp_path / "repo")
    target = installer.hook_path(repo)
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(target.stat().st_mode | stat.S_IXUSR)

    try:
        installer.install_commit_msg_hook(repo, tmp_path / "ldvh")
    except RuntimeError as exc:
        assert "不是 LDVH 管理的 hook" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_status_reports_installed(tmp_path, capsys):
    repo = init_repo(tmp_path / "repo")
    ldvh_root = tmp_path / "ldvh"
    ldvh_root.mkdir()
    installer.install_commit_msg_hook(repo, ldvh_root)

    exit_code = installer.status(repo, ldvh_root)

    assert exit_code == 0
    assert "installed:" in capsys.readouterr().out
