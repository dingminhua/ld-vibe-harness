from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CAPABILITY_BOUNDARY_STATEMENTS = (
    "薄 Skill 对事实写入的保护仅为劝告级：它只能将 AI 路由到 Helper 与行动模板，不能在模型之外机械阻断对 `ldvh-base/` 的直写。",
    "Git Gate 的每一安装实例只覆盖一个实际 Git worktree 中真正触发该 Gate 的 Git 事件；其它 worktree、clone，以及未触发或绕过该 Gate 的行动不在其覆盖范围。",
    "机械检查能够发现来源已定义的机械不合格，不能据此判断事实内容的语义真实性；即使 Schema 合法，语义污染风险仍然存在，未提交污染窗口只能压缩、不能消除。",
)


def test_readme_exposes_environment_neutral_install_deploy_integrate_verify_flow() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert "获取核心 → 安装 → 部署 → 接入 → 验证" in readme
    assert "specs/attachments/09.Att.01-环境接入面.md" in readme
    assert "specs/33-环境安装、部署、接入与验证行动模板.md" in readme
    assert "specs/09-环境接入规范.md" in readme
    assert "ldvh capabilities" in readme
    assert "ldvh-doctor" in readme
    assert "## 启动 Web（本地开发）" in readme
    assert "cd web" in readme
    assert "npm ci" in readme
    assert "npm run dev" in readme
    assert "http://127.0.0.1:5173" in readme
    assert "本地 API 默认使用 `3001`" in readme
    assert "可复制给目标环境 AI 的提示：" in readme
    assert "请阅读 README，完成 LDVH 的安装、部署、接入与验证，并如实报告已验证与未验证的范围。" in readme
    assert "## 给 AI：接入新的开发环境" not in readme


def test_thin_skill_uses_static_distribution_and_both_repository_routes() -> None:
    environment_spec = (REPOSITORY_ROOT / "specs/09-环境接入规范.md").read_text(
        encoding="utf-8"
    )
    integration_surface = (
        REPOSITORY_ROOT / "specs/attachments/09.Att.01-环境接入面.md"
    ).read_text(encoding="utf-8")
    skill = (REPOSITORY_ROOT / "skill/SKILL.md").read_text(encoding="utf-8")
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")

    assert "canonical 模板 `skill/SKILL.md`" in environment_spec
    assert "任何环境的部署件必须与当前发行模板逐字节一致" in environment_spec
    assert "模板不含任何逐环境值，分发即复制文件" in environment_spec

    assert "| `skill-template` | `skill/SKILL.md`（canonical 文件）" in integration_surface
    assert "| 只读复制；模板不含逐环境值" in integration_surface
    assert "安装后包内 `ldvh/_integration_assets/`" in integration_surface
    assert "内容与仓库版逐字节一致" in integration_surface

    work_context_position = skill.index("`ldvh-work-context`")
    action_template_position = skill.index("`ldvh call read-action-template-candidates`")
    assert work_context_position < action_template_position
    assert "`environment-integration-surface`）的 `work-context-core` 行当次内容" in skill

    candidates_position = readme.index("`ldvh call read-action-template-candidates`")
    content_position = readme.index("`ldvh call read-action-template-content`")
    assert candidates_position < content_position
    assert "canonical 模板 `skill/SKILL.md` 逐字节一致" in readme
    assert "├── ldvh-base/" in readme
    assert "├── specs/" in readme


def test_capability_boundaries_are_verbatim_without_expanding_skill_duties() -> None:
    root_spec = (REPOSITORY_ROOT / "specs/00-理念与构成.md").read_text(encoding="utf-8")
    environment_spec = (REPOSITORY_ROOT / "specs/09-环境接入规范.md").read_text(
        encoding="utf-8"
    )
    skill = (REPOSITORY_ROOT / "skill/SKILL.md").read_text(encoding="utf-8")

    for source in (root_spec, environment_spec, skill):
        positions = []
        for statement in CAPABILITY_BOUNDARY_STATEMENTS:
            assert source.count(statement) == 1
            positions.append(source.index(statement))
        assert positions == sorted(positions)

    assert "不增加第四项职责" in environment_spec
    assert "不把 SKILL.md 变成第二规则源" in environment_spec
    assert "本文件不承载规则正文" in skill
    assert "## 能力边界（非职责）" in skill
    assert skill.index("## 职责（只有三件）") < skill.index("## 能力边界（非职责）")
    assert skill.index("## 能力边界（非职责）") < skill.index("## 禁止")


def test_integration_surface_attachment_matches_current_distribution_entry_points() -> None:
    project = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    surfaces = (REPOSITORY_ROOT / "specs/attachments/09.Att.01-环境接入面.md").read_text(encoding="utf-8")

    for entry_point in (
        "ldvh",
        "ldvh-doctor",
        "ldvh-context-recovery",
        "ldvh-git-commit-msg",
        "ldvh-git-hook",
    ):
        assert entry_point in project
        assert f"`{entry_point}`" in surfaces
    assert "统一厂商 payload" in surfaces
    assert "新增 manifest" in surfaces


def test_ai_enablement_guide_keeps_capability_and_evidence_boundaries() -> None:
    template = (REPOSITORY_ROOT / "specs/33-环境安装、部署、接入与验证行动模板.md").read_text(encoding="utf-8")
    environment_spec = (REPOSITORY_ROOT / "specs/09-环境接入规范.md").read_text(encoding="utf-8")

    assert "#### A. 建立目标与当前基线" in template
    assert "不只看" in template
    assert "unverified" in template
    assert "unsupported" in template
    assert "肯定依据证明不存在" in template
    assert "fixture" in template
    assert "逐事件验证矩阵" in template
    assert "薄 Skill 的部署边界" in template
    assert "用户级范围" in template
    assert "Human 受限操作请求" in template
    assert "不得从其它环境、历史记录或名称猜测开关、菜单、manifest、目录、字段或权限模型" in template
    assert "登记一项技能时环境要求提供的字段与输入" in template
    assert "登记或安装一项技能时该环境要求提供的字段与输入" in environment_spec
    assert "该请求不是对 Human 的默认指令，也不构成授权" in template
    assert "Human 完成该操作本身不等于部署成功或真实事件已触发" in template
    assert "执行环境的产品/运行器、版本、平台、实际运行位置和识别依据" in template
    assert "目标环境的产品/运行器、版本、平台、目标位置和识别依据" in template
    assert "同一环境、不同但可访问、不同且当前不可访问或尚未确认" in template
    assert "候选不是目标；不得以多个厂商名称、历史环境或“未配置”替代这一锁定" in template
    assert "Human 目标确认请求" in template
    assert "Human 确认目标本身不等于部署成功或真实事件已触发" in template
    assert "下一责任方；最小动作和需要返回的原始观察；AI 复跑入口" in template
    assert "阻塞本次接入或验收的每个 `unverified`" in template
    assert "目标尚未锁定而交还 **Human 目标确认请求** 时，该交还属于预方案恢复断点，不形成逐事件验证矩阵" in template
    assert "分流到独立 Code 计划" in template
    assert "`unverified` 只表示当次证据不足，不表示以完成接入或验收为目标的行动已经闭合" in environment_spec
    assert "目标尚未锁定时，只能继续无副作用调查，或按 33 交还目标确认请求" in environment_spec
    assert "Human 的确认本身不等于安装、部署、接入或真实触发" in environment_spec
    assert "责任方、恢复动作、原始观察要求或复跑入口" in environment_spec
    assert "Codex" not in template
    assert "Claude" not in template
    assert "Codex" not in environment_spec
    assert "Claude" not in environment_spec
    assert ".codex-plugin" not in template


def test_b4_covers_pre_gate_creation_reviewer_and_post_gate_consumption() -> None:
    checklist = (
        REPOSITORY_ROOT / "specs/attachments/09.Att.02-接入验收行为清单.md"
    ).read_text(encoding="utf-8")
    b4 = checklist[checklist.index("### B4 委派递达") : checklist.index("### B5 恢复与压缩")]

    assert "Human 范围清楚地要求由项目承担并建立/推进 WorkCase" in b4
    assert "自动委派只读 creation Reviewer" in b4
    assert "不为计划准备、只读 creation Reviewer 或 subagent 委派提出专门的 Human 许可请求" in b4
    assert "Gate 1 后，已列明的有界本地动作与只读 Reviewer 委派直接消费同一批准" in b4
    assert "上位环境能力/权限边界、不是 LDVH 的第三个 Human Gate" in b4
    assert "当次无法观察时记 `unverified`" in b4
