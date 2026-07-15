from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ldvh.specs.action_templates import inspect_action_template_sources
from ldvh.specs.repository import inspect_repository

BASELINE_SHA256 = "c3cc446e4823739bca01cdb0e91cb57043cddbe49f9901c4d1065b5d557621cf"
CHARACTERIZATION_SHA256 = "8b7e2122a359fcf894cd1dbe6bc5c6e0e7fa05cdaab5a56f4509da2f8ead9528"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _digest(root: Path, relative: str) -> str:
    return hashlib.sha256((root / relative).read_bytes()).hexdigest()


def test_successor_contract_keeps_identity_time_status_and_dry_run_boundaries(
    current_specs_repository: Path,
) -> None:
    foundation = _read(current_specs_repository, "specs/05-事实模型基础规范.md")
    registry = _read(
        current_specs_repository,
        "specs/attachments/05.Att.01-事实对象统一字段登记.md",
    )

    assert "### 7.4 来源派生的新对象与批量迁移边界" in foundation
    assert "从该类型当前唯一来源允许的合法初态新建" in foundation
    assert "不得为迁移新建“历史”类型、伪状态或专用终态" in foundation
    assert "semantic_payload_sha256" in foundation
    assert "canonical 语义 payload 必须包含目标 `fact_type_key`" in foundation
    assert "只排除 `object_id`、`created_at` 和 `updated_at`" in foundation
    assert "`fact_type_key` 不同的目标必须得到不同语义摘要" in foundation
    assert "目标类型变化必须使既有 dry-run 与 attempt intent 失效" in foundation
    assert "materialized_sha256" in foundation
    assert "不预留身份" in foundation
    assert "不得猜测时区" in foundation
    assert "推进 durable journal 的写入/回读结果" in foundation
    assert "对象和与其同一提交的 receipt 不得预写当次 commit SHA" in foundation
    assert foundation.index("于发布目标前持久化 attempt intent") < foundation.index("原子 no-overwrite 发布目标")
    assert "intent 建立前崩溃最多留下 allocator gap" in foundation
    assert "绑定 logical target key、目标 `fact_type_key`" in foundation

    created_at_row = next(line for line in registry.splitlines() if line.startswith("| `created-at` | `created_at`"))
    assert "同一身份的载体迁移不改变" in created_at_row
    assert "新 successor" in created_at_row
    assert "实际受控创建时间" in created_at_row
    assert "不表示原始源时间" in created_at_row


def test_migration_template_is_discoverable_and_does_not_claim_execution(
    current_specs_repository: Path,
) -> None:
    repository = inspect_repository(current_specs_repository)
    templates = inspect_action_template_sources(repository)
    declarations = {item.template_key: item for item in templates.candidate_declarations}
    declaration = declarations["fact-object-source-reconstruction-migration"]
    source = _read(
        current_specs_repository,
        "specs/34-事实对象来源重建与批量迁移行动模板.md",
    )

    assert repository.issues == ()
    assert templates.issues == ()
    assert declaration.source_key == "fact-object-source-reconstruction-migration-action-template"
    assert declaration.definition_heading.title == "5. 事实对象来源重建与批量迁移行动模板定义"
    for phrase in (
        "固定授权、源闭集与无关基线",
        "logical target plan",
        "全量闭集检查与无写 dry-run",
        "形成批次、应用与恢复",
        "完整回读、关系与 Git anchor",
        "闭集、no-op rerun 与交还",
        "具体 ledger、journal、receipt、batch manifest 的 JSON/YAML 字段或路径",
        "subagent 审核不自动成为某个目标 WorkCase 的 `creation_reviews`",
    ):
        assert phrase in source
    assert source.index("在目标发布前先持久化 durable attempt intent") < source.index(
        "intent 持久化后才原子 no-overwrite 发布目标"
    )
    assert "包含目标 `fact_type_key`、只排除 `object_id/created_at/updated_at`" in source
    assert "`fact_type_key` 不同的目标必须得到不同摘要" in source
    assert "类型变化必须使旧 dry-run 与 intent 失效" in source
    assert "绑定 logical target key、目标 `fact_type_key`" in source


def test_human_decision_semantics_are_recorded_without_advancing_semantic_progress() -> None:
    decision = _read(
        PROJECT_ROOT,
        "docs/v4-architecture/active/V4-V3事实对象全量逐条迁移决定.md",
    )
    characterization = json.loads(_read(PROJECT_ROOT, "migration/v3-facts/source-characterization.json"))

    assert "全部 V4 target 都是当前新建 successor" in decision
    assert "严格使用当前五种 V4 事实类型" in decision
    assert "不猜测时区" in decision
    assert "不新增“历史记录”伪类型或迁移专用终态" in decision
    assert characterization["summary"]["semantic_reviewed_count"] == 0
    assert characterization["summary"]["target_decided_count"] == 0
    assert all(entry["review_state"] == "not_started" for entry in characterization["entries"])


def test_immutable_migration_artifact_identities_remain_frozen() -> None:
    assert _digest(PROJECT_ROOT, "migration/v3-facts/baseline.json") == BASELINE_SHA256
    assert _digest(PROJECT_ROOT, "migration/v3-facts/source-characterization.json") == CHARACTERIZATION_SHA256
