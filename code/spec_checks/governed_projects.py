"""Governed projects configuration checks for LDVH."""

from dataclasses import dataclass
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOVERNED_PROJECTS_FILENAME = "LDVH-GOVERNED-PROJECTS.yaml"
GOVERNED_PROJECTS_ROOT_FIELDS = {"product_name", "product_description", "projects"}
GOVERNED_PROJECTS_ITEM_FIELDS = {"id", "name", "description", "path"}
GOVERNED_PROJECTS_REQUIRED_ITEM_FIELDS = {"id", "path"}


@dataclass
class Issue:
    path: Path
    line: int
    message: str
    code: str = None

    def format(self, root=None):
        display_path = self.path
        if root:
            try:
                display_path = self.path.relative_to(root)
            except ValueError:
                display_path = self.path
        if self.code:
            return f"{display_path}:{self.line}: [{self.code}] {self.message}"
        return f"{display_path}:{self.line}: {self.message}"


def check_root(root):
    root = Path(root)
    path = root / GOVERNED_PROJECTS_FILENAME
    issues = []
    if not path.exists():
        return [
            Issue(
                path,
                1,
                f"工作区根目录缺少管辖项目配置: {GOVERNED_PROJECTS_FILENAME}",
                code="GOVERNED_PROJECTS_MISSING",
            )
        ]
    if not path.is_file():
        return [Issue(path, 1, f"管辖项目配置不是文件: {GOVERNED_PROJECTS_FILENAME}", code="GOVERNED_PROJECTS_NOT_FILE")]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [Issue(path, 1, f"管辖项目配置 YAML 解析失败: {exc}", code="GOVERNED_PROJECTS_YAML_INVALID")]

    if not isinstance(data, dict):
        return [Issue(path, 1, "管辖项目配置根对象必须是 mapping，且只包含 product_name、product_description、projects 字段", code="GOVERNED_PROJECTS_ROOT_INVALID")]

    root_fields = set(data)
    extra_root_fields = sorted(root_fields - GOVERNED_PROJECTS_ROOT_FIELDS)
    missing_root_fields = sorted(GOVERNED_PROJECTS_ROOT_FIELDS - root_fields)
    for field in missing_root_fields:
        issues.append(Issue(path, 1, f"管辖项目配置缺少根字段: {field}", code="GOVERNED_PROJECTS_ROOT_FIELD_MISSING"))
    for field in extra_root_fields:
        issues.append(Issue(path, 1, f"管辖项目配置不得包含根字段: {field}", code="GOVERNED_PROJECTS_ROOT_FIELD_FORBIDDEN"))
    for field in sorted({"product_name", "product_description"} & root_fields):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(Issue(path, 1, f"管辖项目配置根字段 {field} 必须是非空字符串", code="GOVERNED_PROJECTS_ROOT_FIELD_INVALID"))

    projects = data.get("projects")
    if not isinstance(projects, list):
        issues.append(Issue(path, 1, "projects 必须是列表；没有管辖项目时使用空列表", code="GOVERNED_PROJECTS_LIST_INVALID"))
        return issues

    seen_ids = {}
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            issues.append(Issue(path, 1, f"projects[{index}] 必须是对象", code="GOVERNED_PROJECT_ITEM_INVALID"))
            continue
        item_fields = set(project)
        missing_fields = sorted(GOVERNED_PROJECTS_REQUIRED_ITEM_FIELDS - item_fields)
        extra_fields = sorted(item_fields - GOVERNED_PROJECTS_ITEM_FIELDS)
        for field in missing_fields:
            issues.append(Issue(path, 1, f"projects[{index}] 缺少字段: {field}", code="GOVERNED_PROJECT_FIELD_MISSING"))
        for field in extra_fields:
            issues.append(Issue(path, 1, f"projects[{index}] 不得包含字段: {field}", code="GOVERNED_PROJECT_FIELD_FORBIDDEN"))
        for field in sorted(GOVERNED_PROJECTS_ITEM_FIELDS & item_fields):
            value = project.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(Issue(path, 1, f"projects[{index}].{field} 必须是非空字符串", code="GOVERNED_PROJECT_FIELD_INVALID"))
        project_id = project.get("id")
        if isinstance(project_id, str) and project_id.strip():
            normalized_id = project_id.strip()
            if normalized_id in seen_ids:
                first_index = seen_ids[normalized_id]
                issues.append(Issue(path, 1, f"管辖项目 id 重复: {normalized_id}（projects[{first_index}] 与 projects[{index}]）", code="GOVERNED_PROJECT_ID_DUPLICATE"))
            else:
                seen_ids[normalized_id] = index

    return issues


def main(root):
    issues = check_root(root)
    if issues:
        print(f"管辖项目配置检查失败，共 {len(issues)} 个问题：")
        for issue in issues:
            print(f"- {issue.format(PROJECT_ROOT)}")
        return 1
    print("管辖项目配置检查通过。")
    return 0
