# 35A Runtime Protocol Hook 入口补强

文件状态：migration evidence。本文记录 V3 新增 `hooks/LDVH-RUNTIME-PROTOCOL.md` 可见入口的原因、边界和验证。

## 背景

V3 已取消 `rules/` 和 `skills/` 顶层机制，但 Human 指出 Runtime Protocol 仍需要一个明确入口，并要求该入口放在 `hooks/` 下，同时写入 specs。

本阶段确认：

1. 不恢复 `rules/LDVH-RUNTIME-PROTOCOL.md`；
2. 不创建新的顶层 Rules / Skill 机制；
3. Runtime Protocol 可见入口作为 Hook 入口资产放入 `hooks/LDVH-RUNTIME-PROTOCOL.md`；
4. 该入口只写入口身份、权威回指和当前 Code 入口；
5. 该入口不写接入状态；接入状态由 01.Att.04 和 Code 环境审计承接。

## 本阶段处理

1. 新增 `hooks/LDVH-RUNTIME-PROTOCOL.md`，并把内容限制为入口身份、权威回指和当前 Code 入口；
2. 在 `specs/01-保障与衔接.md` 写入 Runtime Protocol 可见入口、`hook_protocol_entry` 边界和该入口文件的允许内容范围；
3. 在 `specs/attachments/01.Att.03-环境入口类型表.md` 增加 `hook_protocol_entry`；
4. 在 `code/environment_entry_audit.py` 中识别 `hooks.runtime-protocol` 候选，状态为 `available`；
5. 补充 `tests/code/test_ldvh_specs_validate.py` 覆盖入口文件、specs 声明和环境审计输出；
6. 同步 `reviews/formal/01.Att.03-formal-review.yaml` hash。

## 边界

本阶段不做：

1. 不声明 Codex、Trae、Claude Code、IDE 或其它环境已自动触发；
2. 不安装、升级、禁用或卸载任何环境插件；
3. 不写入用户级环境 Hook 系统文件；
4. 不改变 Git `commit-msg` Hook 的实现；
5. 不恢复 V2 Rules 或 Skill 顶层机制。

## 验证

本阶段使用 targeted validation：

```bash
python3 code/specs_validate.py all --format text --fail-on-diagnostics
python3 -m pytest tests/code/test_formal_specs.py -q --tb=short
python3 -m pytest tests/code/test_ldvh_specs_validate.py -q -k 'assurance_spec_defines_git_and_environment_hook_boundaries or environment_entry_audit' --tb=short
python3 code/environment_entry_audit.py --format json
git diff --check
```

这些验证只证明 V3 有 Runtime Protocol 可见入口并能被环境审计识别；该入口文件本身不写接入状态，也不证明任何环境 Hook 自动接入。
