from __future__ import annotations

from pathlib import Path

import pytest

from ldvh.specs.field_registry import ADMISSION_AUDIT_PATH, inspect_field_registry
from ldvh.specs.identity import parse_identity
from ldvh.specs.markdown import parse_markdown
from ldvh.specs.repository import inspect_repository


def _inspection(repository: Path):
    repository_inspection = inspect_repository(repository)
    return inspect_field_registry(
        repository_inspection.parsed_documents,
        admission_audit=_admission_audit(repository),
    )


def _admission_audit(repository: Path):
    return parse_markdown(repository / ADMISSION_AUDIT_PATH, ADMISSION_AUDIT_PATH).document


def _synthetic_spark(
    tmp_path: Path,
    *,
    audit_repository: Path,
    omit_admission_for: str | None = None,
    object_id_presence: str = "required",
):
    fields = (
        ("object-id", "object_id", object_id_presence),
        ("fact-type-key", "fact_type_key", "required"),
        ("title", "title", "required"),
        ("created-at", "created_at", "required"),
        ("updated-at", "updated_at", "required"),
        ("status", "status", "forbidden"),
        ("source-refs", "source_refs", "required"),
        ("evidence-refs", "evidence_refs", "forbidden"),
        ("relations", "relations", "conditional"),
    )
    admission_rows = "\n".join(
        f"| 表达 {field_key} 对应的信息需求 | `{field_key}` | reuse | `{field_key}` | "
        "已比较语义、形态、生命周期、来源、出现条件和更新规则，复用现有字段 | "
        "`synthetic-fact-type::5. Synthetic::field-review-0001` |"
        for field_key, _, _ in fields
        if field_key != omit_admission_for
    )
    binding_rows = "\n".join(
        f"| `{field_key}` | {presence} | "
        f"`{'synthetic-fact-type::5. Synthetic' if presence == 'conditional' else 'inherit'}` |"
        for field_key, _, presence in fields
    )
    external_admission_rows = admission_rows.replace(
        "synthetic-fact-type::5. Synthetic::field-review-0001",
        "v4-five-type-closure::five-type-admission-audit::synthetic 字段独立复核::field-review-0001",
    )
    audit_path = audit_repository / ADMISSION_AUDIT_PATH
    audit_text = audit_path.read_text(encoding="utf-8")
    audit_addition = f"""

### synthetic 结构准入记录

本类型没有结构准入事项

### synthetic 字段准入记录

| information_need | compared_field_keys | decision | resulting_field_key | rationale | review_ref |
|---|---|---|---|---|---|
{external_admission_rows}

### synthetic 字段独立复核

| review_key | reviewer | reviewed_scope | findings | disposition |
|---|---|---|---|---|
| `field-review-0001` | independent-ai | 全部 Spark 字段准入行 | 未发现同义重造 | 保留复用结论 |
"""
    next_h2 = "\n## 4. 最终验证"
    assert next_h2 in audit_text
    audit_path.write_text(audit_text.replace(next_h2, audit_addition + next_h2, 1), encoding="utf-8")
    source = f"""# Synthetic 事实类型

```yaml
ldvh_spec:
  spec_key: "synthetic-fact-type"
  spec_id: "29"
  spec_kind: "spec"
  title: "Synthetic 事实类型"
  status: "active"
  canonical_path: "specs/29-Synthetic-事实类型.md"
  parent_spec: "fact-model-foundation"
  relation: "refines"
  positioning: "定义 Spark 事实类型"
  scope: "Spark 事实对象"
  basis:
    - "fact-model-foundation"
  authorized_attachments: []
```

## 1. 价值判断

Spark 需要稳定的事实类型契约。

## 2. 规范依据

以 05 为直接依据。

## 3. 职责边界

只定义 Spark。

## 4. 适用范围

适用于 Spark 事实对象。

## 5. Synthetic

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `synthetic` | 测试使用的合成事实类型 | `synthetic-fact-type::5. Synthetic` |

### 类型专属结构定义

本类型没有类型专属结构

### 准入审计引用

| admission_audit_ref |
|---|
| `v4-five-type-closure::five-type-admission-audit::synthetic::admission-audit` |

### 类型字段使用绑定

| field_key | presence | constraint_ref |
|---|---|---|
{binding_rows}

### 类型专属字段定义

本类型没有类型专属字段

## 6. 验证要求

| 验证对象 | 验证时机 | 成立条件 | 可接受依据 | 验证入口 | 可证明范围 | 未满足时的处理 |
|---|---|---|---|---|---|---|
| Spark 契约 | 变更时 | 机械检查与独立复核成立 | 当前来源和测试 | Helper | 本类型 | 隔离本类型 |

## 7. Human Gate

没有新增 Human Gate。

## 8. Stop Conditions

契约不成立时停止消费。
"""
    path = tmp_path / "specs/29-Synthetic-事实类型.md"
    path.parent.mkdir(exist_ok=True)
    path.write_text(source, encoding="utf-8")
    markdown = parse_markdown(path, "specs/29-Synthetic-事实类型.md")
    assert markdown.issues == ()
    identity = parse_identity(markdown.document)
    assert identity.issues == ()
    assert identity.document is not None
    return identity.document


def test_current_registry_has_unique_resolved_field_definitions(current_specs_repository: Path) -> None:
    inspection = _inspection(current_specs_repository)

    assert inspection.complete is True
    assert inspection.issues == ()
    assert len(inspection.structures) == 8
    assert len(inspection.registrations) == 81
    assert len({registration.field_key for registration in inspection.registrations}) == 81
    assert (
        len({(registration.container_ref, registration.field_path) for registration in inspection.registrations}) == 81
    )
    assert {registration.definition_scope for registration in inspection.registrations} == {"foundation", "type"}
    assert {registration.definition_key for registration in inspection.registrations} == {
        "fact-object-field-registry",
        "adr-fact-type",
        "pitfall-fact-type",
        "spark-fact-type",
        "study-fact-type",
        "workcase-fact-type",
    }
    registrations = {registration.field_key: registration for registration in inspection.registrations}
    for field_key in ("current-summary", "priority"):
        assert registrations[field_key].definition_scope == "foundation"
        assert registrations[field_key].applies_to == ("spark", "workcase")
        assert registrations[field_key].definition_key == "fact-object-field-registry"
    for field_key in ("disposition-summary", "closed-at"):
        assert registrations[field_key].definition_scope == "foundation"
        assert registrations[field_key].applies_to == ("adr", "pitfall", "spark", "study", "workcase")
        assert registrations[field_key].definition_key == "fact-object-field-registry"
    assert registrations["adr-applicability"].definition_scope == "foundation"
    assert registrations["adr-applicability"].applies_to == ("adr", "pitfall", "study")
    assert registrations["adr-applicability"].definition_key == "fact-object-field-registry"
    assert registrations["workcase-validation-summary"].definition_scope == "foundation"
    assert registrations["workcase-validation-summary"].applies_to == ("pitfall", "study", "workcase")
    assert registrations["workcase-validation-summary"].definition_key == "fact-object-field-registry"
    assert registrations["evolution"].definition_scope == "type"
    assert registrations["evolution"].applies_to == ("spark",)
    assert registrations["evolution"].definition_key == "spark-fact-type"
    for field_key in ("study-research-question", "study-abstract"):
        assert registrations[field_key].definition_scope == "type"
        assert registrations[field_key].applies_to == ("study",)
        assert registrations[field_key].definition_key == "study-fact-type"
    assert [definition.fact_type_key for definition in inspection.fact_types] == [
        "spark",
        "workcase",
        "adr",
        "pitfall",
        "study",
    ]


def test_shared_field_requires_at_least_two_sorted_type_bindings(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `object-id` | `fact-object` | `object_id` | string | object-field | `none` | "
            "required | foundation | `*` |",
            "| `object-id` | `fact-object` | `object_id` | string | object-field | `none` | "
            "required | foundation | `spark` |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "部分复用的 foundation 字段必须至少适用于两个事实类型" for issue in inspection.issues)


def test_shared_field_requires_exactly_one_promotion_source(current_specs_repository: Path) -> None:
    workcase = current_specs_repository / ADMISSION_AUDIT_PATH
    text = workcase.read_text(encoding="utf-8")
    workcase.write_text(
        text.replace(
            "| `current-summary,title` | promote | `current-summary` |",
            "| `current-summary,title` | reuse | `current-summary` |",
            1,
        ),
        encoding="utf-8",
    )

    missing = _inspection(current_specs_repository)

    assert missing.complete is False
    assert any(
        "有限共享字段 'current-summary' 必须恰有一个 promote 来源；当前为 none" == issue.summary
        for issue in missing.issues
    )

    workcase.write_text(text, encoding="utf-8")
    spark = current_specs_repository / ADMISSION_AUDIT_PATH
    spark_text = text
    spark.write_text(
        spark_text.replace(
            "| `current-summary,title` | reuse | `current-summary` |",
            "| `current-summary,title` | promote | `current-summary` |",
            1,
        ),
        encoding="utf-8",
    )
    duplicated = _inspection(current_specs_repository)

    assert duplicated.complete is False
    assert any(
        "有限共享字段 'current-summary' 必须恰有一个 promote 来源；当前为 spark, workcase" == issue.summary
        for issue in duplicated.issues
    )


def test_duplicate_structure_admission_information_need_is_rejected(current_specs_repository: Path) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    row = (
        "| 直接读取一项关键语义转折的发生时间和摘要 | "
        "`fact-object,relation,relation-target,source-ref` | new | `spark-evolution-entry` | "
        "已检索全部 current 与 retired 结构；现有结构分别承载完整事实对象、关系、关系目标和来源定位，"
        "均不能无损表达 Spark 内部关键语义转折条目 | "
        "`v4-five-type-closure::five-type-admission-audit::spark 字段独立复核::field-review-0002` |\n"
    )
    source.write_text(text.replace(row, row + row, 1), encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(
        issue.summary == "重复结构 information_need '直接读取一项关键语义转折的发生时间和摘要'"
        for issue in inspection.issues
    )


def test_duplicate_structure_admission_resulting_key_is_rejected(current_specs_repository: Path) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    anchor = (
        "| 直接读取一项关键语义转折的发生时间和摘要 | "
        "`fact-object,relation,relation-target,source-ref` | new | `spark-evolution-entry` | "
        "已检索全部 current 与 retired 结构；现有结构分别承载完整事实对象、关系、关系目标和来源定位，"
        "均不能无损表达 Spark 内部关键语义转折条目 | "
        "`v4-five-type-closure::five-type-admission-audit::spark 字段独立复核::field-review-0002` |\n"
    )
    duplicate_result = (
        "| 保存另一项语义变化结构 | `fact-object` | new | `spark-evolution-entry` | "
        "同一结果结构不得保留第二份准入结论 | "
        "`v4-five-type-closure::five-type-admission-audit::spark 字段独立复核::field-review-0002` |\n"
    )
    source.write_text(text.replace(anchor, anchor + duplicate_result, 1), encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "重复 resulting_structure_key 'spark-evolution-entry'" for issue in inspection.issues)


def _make_evolution_structure_finitely_shared(repository: Path) -> None:
    registry = repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    registry_text = registry.read_text(encoding="utf-8")
    registry_text = registry_text.replace(
        "| `spark-evolution-entry` | object | type | `spark` | "
        "`spark-fact-type::5. Spark 类型定义::spark-evolution-entry` | current |",
        "| `spark-evolution-entry` | object | foundation | `spark,workcase` | "
        "`fact-object-field-registry::跨类型共享结构定义表::spark-evolution-entry` | current |",
        1,
    )
    registry_text = registry_text.replace(
        "存在只供部分类型复用的 `definition_scope: foundation` 结构时，只能在本节追加唯一结构定义，"
        "使用与“基础结构定义表”相同的四列表头。",
        "| structure_key | meaning | not_meaning | constraints |\n"
        "|---|---|---|---|\n"
        "| `spark-evolution-entry` | Spark 与 WorkCase 共享的合成测试结构 | 不表示正式设计 | "
        "只用于结构提升负例 |\n\n"
        "存在只供部分类型复用的 `definition_scope: foundation` 结构时，只能在本节追加唯一结构定义，"
        "使用与“基础结构定义表”相同的四列表头。",
        1,
    )
    registry.write_text(registry_text, encoding="utf-8")

    audit = repository / ADMISSION_AUDIT_PATH
    audit_text = audit.read_text(encoding="utf-8")
    audit_text = audit_text.replace(
        "`fact-object,relation,relation-target,source-ref` | new | `spark-evolution-entry` |",
        "`fact-object,relation,relation-target,source-ref,spark-evolution-entry` | promote | `spark-evolution-entry` |",
        1,
    )
    audit.write_text(audit_text, encoding="utf-8")
    spark = repository / "specs/20-Spark-火花.md"
    spark_text = spark.read_text(encoding="utf-8")
    structure_definition = (
        "| structure_key | meaning | not_meaning | constraints |\n"
        "|---|---|---|---|\n"
        "| `spark-evolution-entry` | Spark 当前摘要无法单独解释时，需要直接读取的一次关键语义转折 | "
        "不表示逐条对话、执行日志、状态历史、来源或证据对象 | 成员闭集只有 `at` 与 `summary`；"
        "只在问题焦点、边界、判断方向或承接方向发生实质变化时增加 |"
    )
    spark.write_text(spark_text.replace(structure_definition, "本类型没有类型专属结构", 1), encoding="utf-8")

    workcase = repository / ADMISSION_AUDIT_PATH
    workcase_text = workcase.read_text(encoding="utf-8")
    admission = (
        "| 复用合成共享结构 | `spark-evolution-entry` | reuse | `spark-evolution-entry` | "
        "合成负例需要第二类型使用同一结构 | "
        "`v4-five-type-closure::five-type-admission-audit::workcase 字段独立复核::field-review-0002` |\n\n"
    )
    workcase_structure_header = (
        "### workcase 结构准入记录\n\n"
        "| information_need | compared_structure_keys | decision | resulting_structure_key | rationale | review_ref |\n"
        "|---|---|---|---|---|---|\n"
    )
    workcase.write_text(
        workcase_text.replace(workcase_structure_header, workcase_structure_header + admission, 1),
        encoding="utf-8",
    )


def test_shared_structure_requires_exactly_one_promotion_source(current_specs_repository: Path) -> None:
    _make_evolution_structure_finitely_shared(current_specs_repository)
    spark = current_specs_repository / ADMISSION_AUDIT_PATH
    spark_text = spark.read_text(encoding="utf-8")
    spark.write_text(
        spark_text.replace("| promote | `spark-evolution-entry` |", "| reuse | `spark-evolution-entry` |", 1),
        encoding="utf-8",
    )

    missing = _inspection(current_specs_repository)

    assert missing.complete is False
    assert any(
        issue.summary == "有限共享结构 'spark-evolution-entry' 必须恰有一个 promote 来源；当前为 none"
        for issue in missing.issues
    )

    spark.write_text(spark_text, encoding="utf-8")
    workcase = current_specs_repository / ADMISSION_AUDIT_PATH
    workcase_text = workcase.read_text(encoding="utf-8")
    workcase.write_text(
        workcase_text.replace(
            "| 复用合成共享结构 | `spark-evolution-entry` | reuse | `spark-evolution-entry` |",
            "| 复用合成共享结构 | `spark-evolution-entry` | promote | `spark-evolution-entry` |",
            1,
        ),
        encoding="utf-8",
    )

    duplicated = _inspection(current_specs_repository)

    assert duplicated.complete is False
    summaries = {issue.summary for issue in duplicated.issues}
    assert "有限共享结构 'spark-evolution-entry' 必须恰有一个 promote 来源；当前为 spark, workcase" in summaries, (
        summaries
    )


def test_duplicate_field_key_is_rejected(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `fact-type-key` | `fact-object` | `fact_type_key` | string | object-field |",
            "| `object-id` | `fact-object` | `fact_type_key` | string | object-field |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "重复 field_key 'object-id'" for issue in inspection.issues)


def test_registry_shape_must_match_the_unique_definition(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `object-id` | `fact-object` | `object_id` | string | object-field | `none` |",
            "| `object-id` | `fact-object` | `object_id` | object | object-field | `none` |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any("登记路径或 JSON 类型与唯一字段定义不一致" in issue.summary for issue in inspection.issues)


def test_invalid_registry_blocks_itself_and_its_authorizing_parent(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `object-id` | `fact-object` | `object_id` | string | object-field | `none` |",
            "| `object-id` | `fact-object` | `object_id` | object | object-field | `none` |",
            1,
        ),
        encoding="utf-8",
    )

    repository = inspect_repository(current_specs_repository)

    assert repository.implemented_checks_complete is False
    assert repository.document_passing_implemented_checks_by_key("fact-object-field-registry") is None
    assert repository.document_passing_implemented_checks_by_key("fact-model-foundation") is None
    assert "fact-object-field-registry" in repository.incomplete_scope
    assert any("登记路径或 JSON 类型与唯一字段定义不一致" in issue.summary for issue in repository.issues)


def test_retired_field_location_cannot_be_reassigned(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    duplicate = (
        "| `legacy-object-id` | `fact-object` | `object_id` | string | object-field | `none` | "
        "required | foundation | `*` | "
        "`fact-object-field-registry::公共顶层字段::legacy-object-id` | retired |\n"
    )
    source.write_text(text.replace("| `fact-type-key`", duplicate + "| `fact-type-key`", 1), encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any("字段位置重复 'fact-object' + 'object_id'" == issue.summary for issue in inspection.issues)


def test_fact_type_bindings_close_over_registry_and_admission_records(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    spark = _synthetic_spark(tmp_path, audit_repository=current_specs_repository)

    inspection = inspect_field_registry(
        (*repository.parsed_documents, spark),
        admission_audit=_admission_audit(current_specs_repository),
    )

    assert inspection.complete is True
    assert [definition.fact_type_key for definition in inspection.fact_types] == [
        "spark",
        "workcase",
        "adr",
        "pitfall",
        "study",
        "synthetic",
    ]


def test_duplicate_admission_information_need_is_rejected(current_specs_repository: Path) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    row = (
        "| 提供 Human 与 AI 可读短标签 | `title` | reuse | `title` | "
        "公共标题只用于识别，不承担失败机制正文 | "
        "`v4-five-type-closure::five-type-admission-audit::pitfall 字段独立复核::field-review-0001` |\n"
    )
    source.write_text(text.replace(row, row + row, 1), encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "重复 information_need '提供 Human 与 AI 可读短标签'" for issue in inspection.issues)


def test_duplicate_admission_resulting_field_key_is_rejected(current_specs_repository: Path) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    anchor = (
        "| 提供 Human 与 AI 可读短标签 | `title` | reuse | `title` | "
        "公共标题只用于识别，不承担失败机制正文 | "
        "`v4-five-type-closure::five-type-admission-audit::pitfall 字段独立复核::field-review-0001` |\n"
    )
    duplicate_result = (
        "| 提供便于列表显示的简短名称 | `title` | reuse | `title` | "
        "同一结果字段不得保留第二份准入结论 | "
        "`v4-five-type-closure::five-type-admission-audit::pitfall 字段独立复核::field-review-0001` |\n"
    )
    source.write_text(text.replace(anchor, anchor + duplicate_result, 1), encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "重复 resulting_field_key 'title'" for issue in inspection.issues)


def test_admission_audit_reference_must_use_the_fixed_record_and_type(
    current_specs_repository: Path,
) -> None:
    source = current_specs_repository / "specs/22-ADR-决策.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "v4-five-type-closure::five-type-admission-audit::adr::admission-audit",
            "other-record::five-type-admission-audit::adr::admission-audit",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary.startswith("准入审计引用必须精确为") for issue in inspection.issues)


@pytest.mark.parametrize("mutation", ["prefixed", "outside", "duplicate"])
def test_admission_audit_record_key_must_be_one_exact_declaration_inside_namespace(
    current_specs_repository: Path,
    mutation: str,
) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    declaration = "> `audit_record_key: v4-five-type-closure`"
    if mutation == "prefixed":
        text = text.replace(declaration, "> `not_audit_record_key: v4-five-type-closure`", 1)
    elif mutation == "outside":
        text = text.replace(declaration, "", 1).replace(
            "## 1. 结论",
            f"{declaration}\n\n## 1. 结论",
            1,
        )
    else:
        text = text.replace(declaration, f"{declaration}\n>\n{declaration}", 1)
    source.write_text(text, encoding="utf-8")

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "准入审计证据必须恰好声明一次稳定 audit_record_key" for issue in inspection.issues)


def test_admission_review_reference_must_resolve_inside_the_same_type_audit(
    current_specs_repository: Path,
) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "spark 字段独立复核::field-review-0002",
            "workcase 字段独立复核::field-review-0002",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    matching = [issue for issue in inspection.issues if issue.summary.startswith("结构 review_ref 未指向")]
    assert matching
    assert matching[0].location.path == ADMISSION_AUDIT_PATH


def test_binding_without_admission_record_is_rejected(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    spark = _synthetic_spark(tmp_path, audit_repository=current_specs_repository, omit_admission_for="relations")

    inspection = inspect_field_registry(
        (*repository.parsed_documents, spark),
        admission_audit=_admission_audit(current_specs_repository),
    )

    assert inspection.complete is False
    assert any(issue.summary == "绑定字段 'relations' 没有字段准入记录" for issue in inspection.issues)


def test_reuse_admission_must_include_resulting_field_in_compared_set(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    _synthetic_spark(tmp_path, audit_repository=current_specs_repository)
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| 表达 object-id 对应的信息需求 | `object-id` | reuse | `object-id` |",
            "| 表达 object-id 对应的信息需求 | none | reuse | `object-id` |",
            1,
        ),
        encoding="utf-8",
    )
    synthetic_source = tmp_path / "specs/29-Synthetic-事实类型.md"
    reparsed = parse_markdown(synthetic_source, "specs/29-Synthetic-事实类型.md")
    identity = parse_identity(reparsed.document)
    assert identity.document is not None
    inspection = inspect_field_registry(
        (*repository.parsed_documents, identity.document),
        admission_audit=_admission_audit(current_specs_repository),
    )

    assert inspection.complete is False
    assert any("reuse 决定必须在 compared_field_keys 中包含结果字段" == issue.summary for issue in inspection.issues)


def test_required_foundation_field_cannot_be_weakened_by_type_binding(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    spark = _synthetic_spark(tmp_path, audit_repository=current_specs_repository, object_id_presence="optional")

    inspection = inspect_field_registry(
        (*repository.parsed_documents, spark),
        admission_audit=_admission_audit(current_specs_repository),
    )

    assert inspection.complete is False
    assert any(issue.summary == "基础必填字段 'object-id' 必须绑定为 required" for issue in inspection.issues)


def test_binding_constraint_ref_must_point_to_same_type_source(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/21-WorkCase-工作项.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `workcase-goal` | required | `inherit` |",
            "| `workcase-goal` | required | `other-source::5. WorkCase 类型定义` |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(
        issue.summary == "绑定字段 'workcase-goal' 的 constraint_ref 必须回指同一类型来源 H2"
        for issue in inspection.issues
    )


def test_binding_constraint_ref_must_resolve_unique_h2(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/21-WorkCase-工作项.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "`workcase-fact-type::6. 对象语义与生命周期`",
            "`workcase-fact-type::不存在的章节`",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(
        issue.summary == "绑定字段 'status' 的 constraint_ref 必须唯一指向同一类型来源 H2"
        for issue in inspection.issues
    )


def test_conditional_binding_cannot_inherit_without_condition_owner(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/21-WorkCase-工作项.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `workcase-blocking-summary` | conditional | `workcase-fact-type::6. 对象语义与生命周期` |",
            "| `workcase-blocking-summary` | conditional | `inherit` |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(
        issue.summary == "conditional 绑定字段 'workcase-blocking-summary' 必须引用出现条件的归口 H2"
        for issue in inspection.issues
    )


def test_type_structure_member_requires_field_admission_record(current_specs_repository: Path) -> None:
    source = current_specs_repository / ADMISSION_AUDIT_PATH
    text = source.read_text(encoding="utf-8")
    source.write_text(
        "\n".join(line for line in text.splitlines() if "记录关键语义转折发生或被确认的时间" not in line) + "\n",
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "类型缺少非全局字段准入记录：evolution-at" for issue in inspection.issues)


def test_structure_definition_ref_must_resolve_exact_structure_row(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "fact-object-field-registry::基础结构定义表::fact-object",
            "fact-object-field-registry::公共顶层字段::fact-object",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(
        "结构 'fact-object' 必须在 definition_ref H2 中恰有一个定义行" == issue.summary for issue in inspection.issues
    )


def test_current_field_cannot_belong_to_retired_container(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "fact-object-field-registry::基础结构定义表::source-ref` | current |",
            "fact-object-field-registry::基础结构定义表::source-ref` | retired |",
            1,
        ),
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any("不得属于 retired container_ref" in issue.summary for issue in inspection.issues)


def test_fact_type_declaration_h3_rejects_extra_content(
    current_specs_repository: Path,
    tmp_path: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    _synthetic_spark(tmp_path, audit_repository=current_specs_repository)
    source = tmp_path / "specs/29-Synthetic-事实类型.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(
        text.replace(
            "| `synthetic` | 测试使用的合成事实类型 | `synthetic-fact-type::5. Synthetic` |\n\n### 类型专属结构定义",
            "| `synthetic` | 测试使用的合成事实类型 | "
            "`synthetic-fact-type::5. Synthetic` |\n\n额外正文\n\n### 类型专属结构定义",
            1,
        ),
        encoding="utf-8",
    )
    reparsed = parse_markdown(source, "specs/29-Synthetic-事实类型.md")
    identity = parse_identity(reparsed.document)
    assert identity.document is not None

    inspection = inspect_field_registry(
        (*repository.parsed_documents, identity.document),
        admission_audit=_admission_audit(current_specs_repository),
    )

    assert inspection.complete is False
    assert any(issue.summary == "事实类型声明 H3 只能包含唯一声明表" for issue in inspection.issues)


def test_attachment_cannot_declare_fact_type(current_specs_repository: Path) -> None:
    source = current_specs_repository / "specs/attachments/05.Att.01-事实对象统一字段登记.md"
    source.write_text(
        source.read_text(encoding="utf-8")
        + """

### 事实类型声明

| fact_type_key | summary | definition_ref |
|---|---|---|
| `fake` | 非法附件声明 | `fact-object-field-registry::Schema 组合边界` |
""",
        encoding="utf-8",
    )

    inspection = _inspection(current_specs_repository)

    assert inspection.complete is False
    assert any(issue.summary == "只有普通 spec 可以包含事实类型声明" for issue in inspection.issues)


def test_type_local_field_error_does_not_invalidate_central_registry(
    current_specs_repository: Path,
) -> None:
    _synthetic_spark(
        current_specs_repository,
        audit_repository=current_specs_repository,
        omit_admission_for="relations",
    )

    repository = inspect_repository(current_specs_repository)

    assert repository.implemented_checks_complete is False
    assert repository.document_passing_implemented_checks_by_key("synthetic-fact-type") is None
    assert repository.document_passing_implemented_checks_by_key("fact-object-field-registry") is not None
    assert repository.document_passing_implemented_checks_by_key("fact-model-foundation") is not None
    assert "synthetic-fact-type" in repository.incomplete_scope
    assert "fact-object-field-registry" not in repository.incomplete_scope
