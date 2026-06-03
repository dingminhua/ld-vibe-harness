import re
import time
from datetime import datetime
from pathlib import Path

from .config import (
    CLOSING_REQUIRED_FIELDS,
    TASK_STATUS_TRANSITIONS,
    VALID_TASK_STATUSES,
    _cache_get,
    _cache_invalidate,
    _cache_set,
    _get_projects,
    _invalidate_cache,
    _log_action,
    _read_yaml_file,
    normalize_task_status,
    read_text,
)


def project_rule_status() -> list[dict]:
    rows = []
    for key, proj in _get_projects().items():
        rule_path = proj["path"] / ".trae" / "rules" / "project_rules.md"
        exists = rule_path.exists()
        text = read_text(rule_path)
        rows.append({
            "project": key,
            "name": proj["name"],
            "exists": exists,
            "has_docs_index": "必读文档索引" in text,
            "has_compression": "压缩保护" in text,
            "path": str(rule_path),
        })
    return rows


def effective_line_count(text: str) -> int:
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---" or re.match(r"^\|[-:| ]+\|$", stripped):
            continue
        count += 1
    return count


def audit_project_rule(project: str, proj: dict) -> dict:
    rule_path = proj["path"] / ".trae" / "rules" / "project_rules.md"
    text = read_text(rule_path)
    findings = []

    def add(code: str, severity: str, title: str, detail: str, suggestion: str):
        findings.append({
            "code": code,
            "severity": severity,
            "title": title,
            "detail": detail,
            "suggestion": suggestion,
        })

    if not rule_path.exists():
        add("RULE_MISSING", "high", "project_rules 缺失", f"未找到 {rule_path}", "为该项目补充 .trae/rules/project_rules.md，并包含项目定位、硬约束、必读文档索引和压缩保护声明。")
        return {
            "project": project,
            "name": proj["name"],
            "path": str(rule_path),
            "exists": False,
            "score": 0,
            "status": "fail",
            "line_count": 0,
            "findings": findings,
        }

    required_sections = {
        "项目定位": "补充项目定位章节，说明该项目的职责。",
        "硬约束": "补充硬约束章节，列出该项目必须遵守的项目级规则。",
        "必读文档索引": "补充必读文档索引，帮助 AI 开工前读取正确事实源。",
        "压缩保护": "补充压缩保护声明，防止上下文压缩后丢失关键规则。",
    }
    for section, suggestion in required_sections.items():
        if section not in text:
            add("SECTION_MISSING", "high", f"缺少{section}", f'{rule_path.name} 未包含"{section}"。', suggestion)

    line_count = effective_line_count(text)
    if line_count > 25:
        add("LINE_LIMIT", "medium", "有效行数超出 L1 建议上限", f"当前有效行数约 {line_count} 行，建议 ≤25 行。", "压缩 project_rules，只保留 L1 关键约束和索引，详细规则移入 docs 或场景规则。")

    if "最后更新" not in text:
        add("DATE_MISSING", "medium", "缺少最后更新日期", '未找到"最后更新"标记。', "在顶部补充最后更新日期，便于判断规则新旧。")

    docs_index_match = re.search(r"## .*必读文档索引([\s\S]*?)(?:\n## |\Z)", text)
    if docs_index_match:
        missing_docs = []
        for doc_id in ["00", "01", "02", "03"]:
            if f"docs/{doc_id}" not in docs_index_match.group(1):
                missing_docs.append(f"docs/{doc_id}")
        if missing_docs:
            add("DOC_INDEX_GAP", "low", "必读文档索引可能不完整", "缺少：" + "、".join(missing_docs), "按项目实际文档结构补充核心 docs 索引，或说明项目无该文档。")

    high = sum(1 for f in findings if f["severity"] == "high")
    medium = sum(1 for f in findings if f["severity"] == "medium")
    low = sum(1 for f in findings if f["severity"] == "low")
    score = max(0, 100 - high * 30 - medium * 12 - low * 5)
    status = "pass" if not findings else "warn" if high == 0 else "fail"

    return {
        "project": project,
        "name": proj["name"],
        "path": str(rule_path),
        "exists": True,
        "score": score,
        "status": status,
        "line_count": line_count,
        "findings": findings,
    }


def audit_project_rules() -> dict:
    results = [audit_project_rule(project, proj) for project, proj in _get_projects().items()]
    total_findings = sum(len(item["findings"]) for item in results)
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "projects": len(results),
            "pass": sum(1 for item in results if item["status"] == "pass"),
            "warn": sum(1 for item in results if item["status"] == "warn"),
            "fail": sum(1 for item in results if item["status"] == "fail"),
            "findings": total_findings,
        },
        "results": results,
    }


def audit_task_base_data() -> dict:
    findings = []

    def add(project_key: str, task_id: str, path: str, severity: str, code: str, detail: str, suggestion: str):
        findings.append({
            "project": project_key,
            "task_id": task_id,
            "path": path,
            "severity": severity,
            "code": code,
            "detail": detail,
            "suggestion": suggestion,
        })

    for project_key, proj in _get_projects().items():
        tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
        if not tasks_dir.exists():
            continue
        known_task_ids = set()
        task_files = sorted(tasks_dir.glob("*.yaml"))
        task_data_by_id = {}
        for task_file in task_files:
            data = _read_yaml_file(task_file)
            task_id = data.get("id", task_file.stem)
            relative_path = str(task_file.relative_to(proj["path"]))
            task_data_by_id[task_id] = data
            if task_id in known_task_ids:
                add(project_key, task_id, relative_path, "high", "DUPLICATE_TASK_ID", "任务 ID 重复", "确保 task-base/tasks 下每个任务 ID 唯一")
            known_task_ids.add(task_id)

        for task_file in task_files:
            data = _read_yaml_file(task_file)
            task_id = data.get("id", task_file.stem)
            relative_path = str(task_file.relative_to(proj["path"]))
            raw_status = data.get("status", "")
            status = normalize_task_status(raw_status)
            if status not in VALID_TASK_STATUSES:
                add(project_key, task_id, relative_path, "high", "INVALID_STATUS", f"非法任务状态：{raw_status}", "将 status 修正为 08 §3.1 定义的标准状态")
                continue

            if status == "Review Needed":
                review = data.get("review") or {}
                if review.get("required") is not True:
                    add(project_key, task_id, relative_path, "high", "REVIEW_REQUIRED_MISSING", "Review Needed 任务未设置 review.required=true", "设置 review.required=true")
                if review.get("status") not in {"pending", "passed", "failed", "needs_human", "skipped"}:
                    add(project_key, task_id, relative_path, "high", "REVIEW_STATUS_INVALID", f"Review Needed 任务 review.status 异常：{review.get('status')}", "设置 review.status 为 pending、passed、failed、needs_human 或 skipped")
                if review.get("status") == "passed" and review.get("human_ready") is not True:
                    add(project_key, task_id, relative_path, "medium", "HUMAN_READY_MISSING", "review.status=passed 但 human_ready 不是 true", "设置 review.human_ready=true 或修正 review.status")

            if status == "Closed":
                if not data.get("closed_at"):
                    add(project_key, task_id, relative_path, "medium", "CLOSED_AT_MISSING", "Closed 任务缺少 closed_at", "补齐 closed_at 或标记历史豁免")
                for field_key, field_label in CLOSING_REQUIRED_FIELDS.items():
                    if not data.get(field_key):
                        add(project_key, task_id, relative_path, "medium", "CLOSING_FIELD_MISSING", f"Closed 任务缺少{field_label}（{field_key}）", "补齐关闭字段或标记历史豁免")
                review = data.get("review") or {}
                if review.get("required", False):
                    review_status = review.get("status")
                    passed = review_status == "passed" and review.get("human_ready") is True
                    skipped = review_status == "skipped" and bool(str(review.get("reason", "")).strip())
                    if not (passed or skipped):
                        add(project_key, task_id, relative_path, "high", "REVIEW_GATE_UNSATISFIED", "Closed 任务未满足 review gate", "确保 review.status=passed 且 human_ready=true，或 review.status=skipped 且填写 reason")

            for dep_id in data.get("dependencies") or []:
                dep_task = task_data_by_id.get(dep_id)
                if not dep_task:
                    add(project_key, task_id, relative_path, "medium", "DEPENDENCY_MISSING", f"依赖任务不存在：{dep_id}", "修正 dependencies 或创建对应任务")
                    continue
                dep_status = normalize_task_status(dep_task.get("status", ""))
                if status in {"Executing", "Review Needed", "Closed"} and dep_status != "Closed":
                    add(project_key, task_id, relative_path, "medium", "DEPENDENCY_NOT_CLOSED", f"当前状态为 {status}，但依赖 {dep_id} 未关闭", "先关闭依赖任务，或回退当前任务状态")

    severity_order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda item: (severity_order.get(item["severity"], 9), item["project"], item["task_id"], item["code"]))
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "findings": len(findings),
            "high": sum(1 for item in findings if item["severity"] == "high"),
            "medium": sum(1 for item in findings if item["severity"] == "medium"),
            "low": sum(1 for item in findings if item["severity"] == "low"),
        },
        "findings": findings,
    }
def _check_task_check_trigger(task_data: dict) -> bool:
    status = task_data.get("status", "")
    review = task_data.get("review", {})
    review_status = review.get("status", "")

    return (
        status == "Review Needed"
        and review_status == "pending"
    )


def _perform_task_check(task_data: dict) -> dict:
    from .taskbase import _load_task_base_task_details
    task_id = task_data.get("id", "")
    title = task_data.get("title", "")
    findings = []
    passed = True

    def add_finding(severity: str, type_: str, description: str, suggested_fix: str):
        nonlocal passed
        if severity in ["high", "medium"]:
            passed = False
        findings.append({
            "severity": severity,
            "type": type_,
            "description": description,
            "suggested_fix": suggested_fix,
        })

    acceptance = task_data.get("acceptance", "")
    if not acceptance or not acceptance.strip():
        add_finding("high", "MISSING_ACCEPTANCE", "缺少验收标准", "补充明确的验收标准到 acceptance 字段")

    closing_fields = {
        "completion_summary": "完成摘要",
        "validation_result": "验证结果",
        "closure_evidence": "关闭证据",
        "acceptance_result": "验收结果",
    }
    for field, label in closing_fields.items():
        if not task_data.get(field, ""):
            add_finding("high", f"MISSING_{field.upper()}", f"缺少{label}", f"补齐 {label} 字段")

    review = task_data.get("review", {})
    if not review.get("required", False):
        add_finding("medium", "CHECK_NOT_REQUIRED", "未启用检查", "设置 review.required = true 以启用自动检查")

    tasks = _load_task_base_task_details("self", _get_projects()["self"])
    dependencies = task_data.get("dependencies", [])
    for dep_id in dependencies:
        dep_task = next((t for t in tasks if t.get("id") == dep_id), None)
        if dep_task and dep_task.get("normalized_status") not in ["Closed"]:
            add_finding("medium", "DEPENDENCY_NOT_CLOSED", f"依赖任务 {dep_id} 未完成", "等待依赖任务完成后再进行检查")

    status = "passed" if passed else "failed"
    summary = "检查通过" if passed else f"检查发现 {len(findings)} 个问题"

    return {
        "task_id": task_id,
        "task_title": title,
        "status": status,
        "summary": summary,
        "findings": findings,
        "checked_at": datetime.now().isoformat(),
        "human_ready": passed,
        "next_action": "human_gate" if passed else "decision_needed",
    }


def _update_task_review_status(project_key: str, task_id: str, check_result: dict):
    import yaml
    proj = _get_projects().get(project_key)
    if not proj:
        return
    tasks_dir = proj["path"] / proj.get("task_base", "task-base") / "tasks"
    task_path = tasks_dir / f"{task_id}.yaml"
    if not task_path.exists():
        return

    data = _read_yaml_file(task_path)
    review = data.get("review", {})
    review["status"] = check_result["status"]
    review["summary"] = check_result["summary"]
    review["findings"] = check_result["findings"]
    review["checked_at"] = check_result["checked_at"]
    review["human_ready"] = check_result["human_ready"]
    review["next_action"] = check_result["next_action"]

    data["review"] = review
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d")

    with open(task_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    _invalidate_cache()
    _log_action("review_check", task_id, f"检查结果: {check_result['status']}")


def _trigger_pending_task_checks() -> list[dict]:
    from .taskbase import _load_task_base_task_details
    results = []
    for project_key, proj in _get_projects().items():
        tasks = _load_task_base_task_details(project_key, proj)
        for task in tasks:
            if _check_task_check_trigger(task):
                check_result = _perform_task_check(task)
                results.append(check_result)
                _update_task_review_status(project_key, task["id"], check_result)
    return results
