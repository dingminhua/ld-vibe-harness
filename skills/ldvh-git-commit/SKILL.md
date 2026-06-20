---
name: ldvh-git-commit
description: Prepare, validate, and create LDVH Git commits under specs/10. Use when Codex is asked to commit LDVH changes, write or repair a commit message, split staged changes, run commit prechecks, or explain/fix commit validation failures in an LDVH governed repository.
---

# LDVH Git Commit

```yaml
ldvh_asset:
  id: "ldvh-git-commit"
  type: "skill"
  status: "active"
  canonical_path: "skills/ldvh-git-commit/SKILL.md"
  source_specs:
    - "specs/10-Git提交规范.md"
    - "specs/04.02-LDVH能力资产与落地保障规范.md"
  consumption_scenarios:
    - "AI 准备创建 Git commit"
    - "提交消息预检失败修正"
    - "提交事实源修改前的拆分与说明生成"
  inputs:
    - "用户提交目标"
    - "git status / staged files"
    - "验证命令结果"
  outputs:
    - "符合 specs/10 的 commit message"
    - "提交前预检结果"
    - "提交后 hash 和剩余工作区状态"
  handoff: "完成 commit 后交还主控；预检失败、拆分不确定或涉及 Human Gate 时暂停。"
  verification:
    - "python3 /Users/dmh2002/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ldvh-git-commit"
    - "python3 code/commit_validate.py --check-message '<message>' --files <files>"
    - "python3 code/specs_validate.py deployment-entries"
  sync_triggers:
    - "specs/10-Git提交规范.md commit message 契约变化"
    - "code/commit_validate.py CLI 或错误等级变化"
    - "hooks/ldvh-hooks.yaml git.commit-msg 事件变化"
    - "specs/04.02-LDVH能力资产与落地保障规范.md Skill 资产规则变化"
  deprecation: "废弃或重命名前必须同步 04.02、10、0074、memo-0017 和 deployment-entries。"
```

Use this Skill to convert `specs/10-Git提交规范.md` into the commit execution workflow. Do not create new commit rules here. Treat `specs/10-Git提交规范.md` as the canonical rule, `code/commit_validate.py` as the canonical validator, `hooks/ldvh-hooks.yaml` as the Hook event registry, and `code/hook_dispatch.py` as the unified dispatcher.

## Workflow

1. Read the relevant parts of `specs/10-Git提交规范.md`: format, body requirements, type/scope selection, AI execution order, verification, risk, and Human Gate boundaries.
2. Inspect `git status --short` and staged files. Include only files that belong to the requested commit; never stage unrelated user changes.
3. Decide whether to split commits. Split independent intents. Keep one atomic closure together when specs, Code, tests, hooks, rules, or skills are all part of the same landing.
4. Choose one `type` and zero or one `scope`. Write the description in Simplified Chinese and make it state the concrete result.
5. Write a body when required by specs/10, especially for specs, rules, code, tests, web, hooks, skills, agents, config, multiple files, Human Gate context, validation, risk, or cross-source changes. Prefer headings: `动机`, `关键变更`, `影响边界`, `验证结论`, `风险与后续`.
6. Precheck the message before committing:

```bash
python3 code/commit_validate.py --check-message-file <message-file> --files <staged-files>
```

If no message file exists, use:

```bash
python3 code/commit_validate.py --check-message '<message>' --files <staged-files>
```

When validating through the unified Hook entry, use:

```bash
python3 code/hook_dispatch.py run git.commit-msg --message-file <message-file>
```

7. Run verification commands that match the changed surface. Prefer focused tests for narrow changes and broader checks for shared specs, validators, hooks, or asset registration.
8. Fix all precheck errors before committing. Treat warnings as review prompts: refine the body, record a justified residual risk, or pause for Human judgment when needed.
9. Commit with the validated message. After committing, report the commit hash and the remaining `git status --short`.

## Boundaries

- Do not replace `specs/10-Git提交规范.md`, Git commit records, Code validation, Human Gate, CI, or the unified Hook registry.
- Do not use LDVH-private trailers such as `Human-Gate:`, `Verification:`, or `Risk:` as a substitute for body semantics.
- Do not claim an environment hook is installed or active merely because `hooks/ldvh-hooks.yaml` exists.
- Do not modify native Git hook registration, user hook managers, IDE settings, Codex settings, or CI configuration unless the user explicitly asks for that environment adaptation.
- Stop when staged changes are unrelated, split boundaries are unclear, validation must be bypassed, destructive Git operations are needed, or the commit would change environment installation state.
