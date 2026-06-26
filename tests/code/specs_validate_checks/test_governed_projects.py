import subprocess
import sys
from pathlib import Path

from .common import checker, write_md


PROJECT_ROOT = Path(__file__).resolve().parents[3]

# ══════════════════════════════════════════════════════════════════════
# governed-projects — 工作区根目录管辖项目配置检查
# ══════════════════════════════════════════════════════════════════════


def write_governed_projects(root, content):
    return write_md(root / "LDVH-GOVERNED-PROJECTS.yaml", content)


def governed_project_codes(issues):
    return [issue.code for issue in issues]


def test_governed_projects_empty_list_passes(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
projects: []
""",
    )

    assert checker.governed_projects_check_root(tmp_path) == []


def test_governed_projects_multiple_projects_pass(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理多个项目。
projects:
  - id: app-web
    path: /Users/me/projects/app-web
    name: App Web
    description: |
      前端项目。
  - id: app-api
    path: /Users/me/projects/app-api
""",
    )

    assert checker.governed_projects_check_root(tmp_path) == []


def test_governed_projects_git_identity_passes(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理多个项目。
projects:
  - id: app-web
    path: /Users/me/projects/app-web
    git:
      common_dir: /Users/me/projects/app-web/.git
      remote_url: https://github.com/example/app-web.git
      default_branch: main
""",
    )

    assert checker.governed_projects_check_root(tmp_path) == []


def test_governed_projects_product_fields_are_required(tmp_path):
    write_governed_projects(tmp_path, "projects: []")

    codes = governed_project_codes(checker.governed_projects_check_root(tmp_path))

    assert "GOVERNED_PROJECTS_ROOT_FIELD_MISSING" in codes


def test_governed_projects_duplicate_id_is_reported(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
projects:
  - id: app
    name: App One
    description: One
    path: /tmp/app-one
  - id: app
    name: App Two
    description: Two
    path: /tmp/app-two
""",
    )

    issues = checker.governed_projects_check_root(tmp_path)

    assert "GOVERNED_PROJECT_ID_DUPLICATE" in governed_project_codes(issues)


def test_governed_projects_extra_fields_are_reported(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
version: 1
projects:
  - id: app
    name: App
    description: App project
    path: /tmp/app
    type: governed_project
""",
    )

    codes = governed_project_codes(checker.governed_projects_check_root(tmp_path))

    assert "GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN" in codes
    assert "GOVERNED_PROJECT_FIELD_FORBIDDEN" in codes


def test_governed_projects_git_extra_fields_are_reported(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
projects:
  - id: app
    name: App
    description: App project
    path: /tmp/app
    git:
      common_dir: /tmp/app/.git
      status: active
""",
    )

    codes = governed_project_codes(checker.governed_projects_check_root(tmp_path))

    assert "GOVERNED_PROJECT_GIT_FIELD_FORBIDDEN" in codes


def test_governed_projects_script_fast_path_outputs_text(tmp_path):
    write_governed_projects(
        tmp_path,
        """
product_name: LD Vibe Harness
product_description: |
  管理当前工作区项目。
projects: []
""",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "code" / "specs_validate.py"),
            "governed-projects",
            "--root",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "管辖项目配置检查通过。" in result.stdout
    assert result.stderr == ""
