from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


H2_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
H3_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)

DEFAULT_PATTERNS = [
    "本文解决的问题",
    "上位依据",
    "构成要素归属与价值判断",
    "正向价值判断",
    "逆向价值判断",
    "事实源边界",
    "Human Gate",
    "Code",
    "知识地图",
    "不得",
    "不定义",
]

ACTION_MEMBER_PREFIXES = {"30", "31", "32", "34", "35", "36"}
FACT_MEMBER_PREFIXES = {"20", "21", "22", "23", "24"}


def scan_specs(specs_root: str | Path, patterns: list[str] | None = None) -> dict[str, Any]:
    root = Path(specs_root)
    body_specs = sorted(root.glob("*.md"))
    active_patterns = patterns or DEFAULT_PATTERNS
    files = [_scan_file(path, active_patterns) for path in body_specs]

    repeated_h2 = _repeated_h2(files)
    families = _family_skeletons(files)
    pattern_summary = _pattern_summary(files, active_patterns)

    return {
        "body_spec_count": len(body_specs),
        "files": files,
        "repeated_h2": repeated_h2,
        "families": families,
        "pattern_summary": pattern_summary,
        "bloat_candidates": _bloat_candidates(repeated_h2, families, pattern_summary),
    }


def _scan_file(path: Path, patterns: list[str]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    h2 = [_normalize_heading(match.group(1)) for match in H2_RE.finditer(text)]
    h3 = [_normalize_heading(match.group(1)) for match in H3_RE.finditer(text)]
    return {
        "name": path.name,
        "prefix": path.name[:2],
        "char_count": len(text),
        "h2": h2,
        "h2_count": len(h2),
        "h3_count": len(h3),
        "pattern_counts": {pattern: text.count(pattern) for pattern in patterns},
    }


def _repeated_h2(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    for item in files:
        for heading in item["h2"]:
            counter[heading] += 1
            examples.setdefault(heading, []).append(item["name"])
    return [
        {
            "heading": heading,
            "file_count": count,
            "examples": examples[heading][:8],
        }
        for heading, count in counter.most_common()
        if count >= 3
    ]


def _family_skeletons(files: list[dict[str, Any]]) -> dict[str, Any]:
    by_prefix = {item["prefix"]: item for item in files}
    action = [
        by_prefix[prefix]
        for prefix in sorted(ACTION_MEMBER_PREFIXES)
        if prefix in by_prefix
    ]
    fact = [
        by_prefix[prefix]
        for prefix in sorted(FACT_MEMBER_PREFIXES)
        if prefix in by_prefix
    ]
    return {
        "action_members_30_31_32_34_35_36": _skeleton_summary(action),
        "fact_members_20_24": _skeleton_summary(fact),
    }


def _skeleton_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    if not items:
        return {"file_count": 0, "common_prefix_length": 0, "common_h2": []}
    common = list(items[0]["h2"])
    for item in items[1:]:
        common = [
            left
            for left, right in zip(common, item["h2"])
            if left == right
        ][: _shared_prefix_length(common, item["h2"])]
    return {
        "file_count": len(items),
        "files": [item["name"] for item in items],
        "common_prefix_length": len(common),
        "common_h2": common,
    }


def _shared_prefix_length(left: list[str], right: list[str]) -> int:
    count = 0
    for l_item, r_item in zip(left, right):
        if l_item != r_item:
            break
        count += 1
    return count


def _pattern_summary(
    files: list[dict[str, Any]], patterns: list[str]
) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for pattern in patterns:
        hit_files = [
            item
            for item in files
            if item["pattern_counts"].get(pattern, 0) > 0
        ]
        summary.append(
            {
                "pattern": pattern,
                "file_count": len(hit_files),
                "total_count": sum(item["pattern_counts"][pattern] for item in hit_files),
                "top_files": [
                    {
                        "name": item["name"],
                        "count": item["pattern_counts"][pattern],
                    }
                    for item in sorted(
                        hit_files,
                        key=lambda found: found["pattern_counts"][pattern],
                        reverse=True,
                    )[:8]
                ],
            }
        )
    return summary


def _bloat_candidates(
    repeated_h2: list[dict[str, Any]],
    families: dict[str, Any],
    pattern_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    h2_by_name = {item["heading"]: item for item in repeated_h2}
    patterns = {item["pattern"]: item for item in pattern_summary}
    return [
        {
            "candidate": "universal_governance_sections",
            "evidence": [
                h2_by_name[name]
                for name in ["本文解决的问题", "规范保障要求", "Human Gate", "待补齐事项"]
                if name in h2_by_name
            ],
            "likely_action": "Keep headings as parseable skeleton, move repeated generic guidance to parent rules or generated Action Guide diagnostics.",
        },
        {
            "candidate": "action_member_template_duplication",
            "evidence": families["action_members_30_31_32_34_35_36"],
            "likely_action": "Use 03 parent/member template as the authority; child action specs should carry only action-specific deltas and anchors.",
        },
        {
            "candidate": "fact_member_template_duplication",
            "evidence": families["fact_members_20_24"],
            "likely_action": "Use 02 parent/member template as the authority; child object specs should carry object-specific state, fields, gates, and relations.",
        },
        {
            "candidate": "cross_cutting_boundary_repetition",
            "evidence": [
                patterns[name]
                for name in ["事实源边界", "Human Gate", "不得", "不定义"]
                if name in patterns
            ],
            "likely_action": "Separate global boundary rules from local exceptions; let Code/Action Guide project repeated stop conditions.",
        },
        {
            "candidate": "legacy_knowledge_map_wording",
            "evidence": [patterns["知识地图"]] if "知识地图" in patterns else [],
            "likely_action": "Rename or project to Action Guide concepts carefully without rewriting all specs at once.",
        },
    ]


def _normalize_heading(heading: str) -> str:
    return re.sub(r"^\d+(?:\.\d+)*\.\s*", "", heading.strip())
