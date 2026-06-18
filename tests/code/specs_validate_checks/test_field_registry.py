from .common import checker, write_md
from spec_checks import field_registry as field_registry_checks


REGISTRY_HEADER = (
    "| field_path | scope | meaning | format_kind | value_shape | ref_kind | enum_owner | "
    "schema_owner | code_check_kind | web_render_kind | status | replacement |"
)


def registry_table(rows):
    return "\n".join([REGISTRY_HEADER, "|---|---|---|---|---|---|---|---|---|---|---|---|", *rows])


def legacy_table(rows):
    return "\n".join(
        [
            "| 旧字段或名称 | 状态 | 替代或迁移指向 | 说明 |",
            "|---|---|---|---|",
            *rows,
        ]
    )


def write_registry_doc(path, common_rows=None, object_rows=None, legacy_rows=None):
    common_rows = common_rows or [
        "| `description` | common | 背景 | narrative | markdown | none | none | 05.01 | format | summary | active | none |"
    ]
    object_rows = object_rows or [
        "| `success_criteria` | workplan | 成功标准 | checklist | checklist_markdown | none | none | 21 | owner_state | checklist | active | none |"
    ]
    legacy_rows = legacy_rows or [
        "| `tasks` | deprecated field | `orchestration.execution_items` | 旧 TaskPlan 下的 Task 列表 |"
    ]
    return write_md(
        path,
        f"""
# 工作字段内容格式规范

## 5. 字段内容/消费注册表

### 5.4 通用字段注册

{registry_table(common_rows)}

### 5.5 对象特有字段注册

{registry_table(object_rows)}

### 5.6 旧 TaskPlan / Task 字段废弃与别名映射

{legacy_table(legacy_rows)}
""",
    )


def test_field_registry_core_implementation_lives_in_spec_checks():
    assert checker.field_registry_checks is field_registry_checks
    assert field_registry_checks.check_paths.__module__ == "spec_checks.field_registry"
    assert field_registry_checks.main.__module__ == "spec_checks.field_registry"


def test_field_registry_accepts_valid_registry(tmp_path):
    path = write_registry_doc(tmp_path / "05.01-工作字段内容格式规范.md")

    assert checker.field_registry_check([str(path)]) == []


def test_field_registry_accepts_collection_owner(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.01-工作字段内容格式规范.md",
        common_rows=[
            "| `source` | common | 输入来源 | reference | string | mixed_ref | none | 20-39 | ref | summary | active | none |"
        ],
    )

    assert checker.field_registry_check([str(path)]) == []


def test_field_registry_accepts_mixed_ref_and_enum_signal_web_kinds(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.01-工作字段内容格式规范.md",
        object_rows=[
            "| `orchestration.mode` | workplan | 编排方式 | reference | string | enum | 21 | 21 | enum | enum_signal | active | none |",
            "| `orchestration.execution_items.input_refs` | workplan | 输入引用 | reference | list_string | mixed_ref | none | 21 | ref | mixed_ref | active | none |",
        ],
    )

    assert checker.field_registry_check([str(path)]) == []


def test_field_registry_reports_invalid_enum(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.01-工作字段内容格式规范.md",
        common_rows=[
            "| `description` | common | 背景 | prose | markdown | none | none | 05.01 | format | summary | active | none |"
        ],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_FORMAT_INVALID" for issue in issues)


def test_field_registry_reports_duplicate_scope_and_path(tmp_path):
    duplicated = "| `description` | common | 背景 | narrative | markdown | none | none | 05.01 | format | summary | active | none |"
    path = write_registry_doc(
        tmp_path / "05.01-工作字段内容格式规范.md",
        common_rows=[duplicated, duplicated],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_DUPLICATE" for issue in issues)


def test_field_registry_reports_active_replacement(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.01-工作字段内容格式规范.md",
        common_rows=[
            "| `description` | common | 背景 | narrative | markdown | none | none | 05.01 | format | summary | active | `details` |"
        ],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_REPLACEMENT_INVALID" for issue in issues)


def test_field_registry_reports_workplan_field_missing_from_registry(tmp_path):
    registry_path = write_registry_doc(tmp_path / "05.01-工作字段内容格式规范.md")
    write_md(
        tmp_path / "21-WorkPlan-工作计划.md",
        """
# WorkPlan-工作计划

## 6. 字段契约

| 字段名 | 含义 | 类型 | 必填 |
|---|---|---|---|
| `description` | 说明 | string | 是 |
| `unregistered_field` | 未注册字段 | string | 否 |
""",
    )

    issues = checker.field_registry_check([str(registry_path)])

    assert any(issue.code == "FIELD_REGISTRY_WORKPLAN_FIELD_MISSING" for issue in issues)
    assert any("unregistered_field" in issue.message for issue in issues)


def test_field_registry_reports_legacy_status_invalid(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.01-工作字段内容格式规范.md",
        legacy_rows=[
            "| `tasks` | legacy | `orchestration.execution_items` | 旧 TaskPlan 下的 Task 列表 |"
        ],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_LEGACY_STATUS_INVALID" for issue in issues)
