from .common import checker, write_md
from spec_checks import field_registry as field_registry_checks


REGISTRY_HEADER = (
    "| field_path | scope | meaning | format_kind | value_shape | ref_kind | enum_owner | "
    "schema_owner | code_check_kind | web_render_kind | status | replacement |"
)


def registry_table(rows):
    return "\n".join([REGISTRY_HEADER, "|---|---|---|---|---|---|---|---|---|---|---|---|", *rows])


def write_registry_doc(path, common_rows=None, object_rows=None):
    common_rows = common_rows or [
        "| `description` | common | 背景 | narrative | markdown | none | none | 05.02 | format | summary | active | none |"
    ]
    object_rows = object_rows or [
        "| `success_criteria` | workcase | 成功标准 | checklist | checklist_markdown | none | none | 21 | owner_state | checklist | active | none |"
    ]
    return write_md(
        path,
        f"""
# 工作模型字段注册与消费规范

## 3. 字段注册表

### 3.4 通用字段注册

{registry_table(common_rows)}

### 3.5 对象特有字段注册

{registry_table(object_rows)}

""",
    )


def test_field_registry_core_implementation_lives_in_spec_checks():
    assert checker.field_registry_checks is field_registry_checks
    assert field_registry_checks.check_paths.__module__ == "spec_checks.field_registry"
    assert field_registry_checks.main.__module__ == "spec_checks.field_registry"


def test_field_registry_accepts_valid_registry(tmp_path):
    path = write_registry_doc(tmp_path / "05.03-工作模型字段注册与消费规范.md")

    assert checker.field_registry_check([str(path)]) == []


def test_field_registry_accepts_collection_owner(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.03-工作模型字段注册与消费规范.md",
        common_rows=[
            "| `source` | common | 输入来源 | reference | string | mixed_ref | none | 20-39 | ref | summary | active | none |"
        ],
    )

    assert checker.field_registry_check([str(path)]) == []


def test_field_registry_accepts_mixed_ref_url_ref_and_enum_signal_web_kinds(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.03-工作模型字段注册与消费规范.md",
        object_rows=[
            "| `orchestration.mode` | workcase | 编排方式 | reference | string | enum | 21 | 21 | enum | enum_signal | active | none |",
            "| `orchestration.execution_items.input_refs` | workcase | 输入引用 | reference | list_string | mixed_ref | none | 21 | ref | mixed_ref | active | none |",
            "| `urls` | study | 外部网址 | reference | list_object | url_ref | none | 24 | structured | url_ref | active | none |",
        ],
    )

    assert checker.field_registry_check([str(path)]) == []


def test_field_registry_reports_scope_owner_mismatch(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.03-工作模型字段注册与消费规范.md",
        object_rows=[
            "| `urls` | study | 外部网址 | reference | list_object | url_ref | none | 26 | structured | url_ref | active | none |",
        ],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_OWNER_SCOPE_MISMATCH" for issue in issues)


def test_field_registry_reports_invalid_enum(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.03-工作模型字段注册与消费规范.md",
        common_rows=[
            "| `description` | common | 背景 | prose | markdown | none | none | 05.02 | format | summary | active | none |"
        ],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_FORMAT_INVALID" for issue in issues)


def test_field_registry_reports_duplicate_scope_and_path(tmp_path):
    duplicated = "| `description` | common | 背景 | narrative | markdown | none | none | 05.02 | format | summary | active | none |"
    path = write_registry_doc(
        tmp_path / "05.03-工作模型字段注册与消费规范.md",
        common_rows=[duplicated, duplicated],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_DUPLICATE" for issue in issues)


def test_field_registry_reports_active_replacement(tmp_path):
    path = write_registry_doc(
        tmp_path / "05.03-工作模型字段注册与消费规范.md",
        common_rows=[
            "| `description` | common | 背景 | narrative | markdown | none | none | 05.02 | format | summary | active | `details` |"
        ],
    )

    issues = checker.field_registry_check([str(path)])

    assert any(issue.code == "FIELD_REGISTRY_REPLACEMENT_INVALID" for issue in issues)


def test_field_registry_reports_workcase_field_missing_from_registry(tmp_path):
    registry_path = write_registry_doc(tmp_path / "05.03-工作模型字段注册与消费规范.md")
    write_md(
        tmp_path / "21-WorkCase-工作项.md",
        """
# WorkCase-工作项

## 6. 字段契约

| 字段名 | 含义 | 类型 | 必填 |
|---|---|---|---|
| `description` | 说明 | string | 是 |
| `unregistered_field` | 未注册字段 | string | 否 |
""",
    )

    issues = checker.field_registry_check([str(registry_path)])

    assert any(issue.code == "FIELD_REGISTRY_WORKCASE_FIELD_MISSING" for issue in issues)
    assert any("unregistered_field" in issue.message for issue in issues)
