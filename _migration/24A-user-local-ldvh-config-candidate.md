# 24A 用户级 LDVH 配置目录候选记录

文件状态：candidate note / transferred。本文只记录 Human 讨论形成的后续设计候选，不授权当前实现改变配置解析顺序，不新增正式配置事实源。2026-07-02 已按 Human 确认转入 `ldvh-base/sparks/spark-0041-user-local-ldvh-config-directory.yaml`；本文保留为迁移证据和来源说明。

## 背景

当前 V3 管辖项目配置由 `specs/10-安装与配置规范.md` 定义，默认事实源是 repo / workspace 中的 `LDVH-GOVERNED-PROJECTS.yaml`。Human 进一步提出：如果配置文件总放在仓库或上级工作区，跨项目、单机绝对路径和用户本地默认值会出现放置位置问题，可以考虑建立用户级 LDVH 配置目录。

## 初步判断

可以考虑建立用户级配置目录，但不应直接替代现有 repo / workspace 级配置。当前更稳定的方向是：配置生成时必须先让 Human 选择放置位置，推荐放在 LDVH 工作区根目录。

建议把配置分为两类：

1. 共享配置：继续由 repo / workspace 中的 `LDVH-GOVERNED-PROJECTS.yaml` 承接，适合提交、审核、团队共享和 V3 自身管辖登记。
2. 用户本机配置：由用户级 LDVH 配置目录承接，适合本机绝对路径、默认 governance root、个人项目登记、缓存和临时状态。

用户级配置目录不得承载 specs、事实对象正式实例、Human Gate 结论、Hook 安装授权或环境入口 integrated 状态。

## 配置生成位置选择候选

后续若新增配置生成入口，不得静默写入固定目录。生成 `LDVH-GOVERNED-PROJECTS.yaml` 前必须让 Human 明确选择放置位置，并至少提供以下三个选项：

1. 工作区根目录，推荐选项。默认候选位置是 LDVH 安装目录的上一级目录，也就是与 LDVH 项目并行的目录。例如 LDVH 安装在 `/Users/example/workspace/ld-vibe-harness-v3` 时，默认工作区根目录候选为 `/Users/example/workspace/`。
2. 用户级 LDVH 配置目录，例如 macOS / Linux 的 `~/.ldvh` 或 Windows 的 `%APPDATA%\ldvh`。该选项适合单机默认值、路径指针或个人登记，但不得静默覆盖工作区级配置。
3. 当前项目根目录。该选项适合单项目自管，但如果当前工作区存在多个管辖项目，不应作为默认推荐。

选择界面必须把“工作区根目录”放在推荐位置，并说明推荐理由：它能同时覆盖 LDVH 项目和多个并行管辖项目，便于 target/cwd 向上发现，也避免把主配置藏进用户系统目录或某个单独项目。

若用户选择用户级目录，后续仍应区分“用户级目录保存主配置”与“用户级目录只保存默认工作区指针”。当前更保守的候选是：用户级目录优先保存默认工作区位置或个人默认值，主 `LDVH-GOVERNED-PROJECTS.yaml` 推荐仍放在工作区根目录。

## 跨平台目录候选

后续正式设计不应只写死 `~/.ldvh`。建议定义逻辑目录 `LDVH_USER_HOME`，并按以下顺序解析：

1. 显式环境变量 `LDVH_HOME`，最高优先级；
2. Windows 配置默认目录：`%APPDATA%\ldvh`；
3. Windows 缓存或临时状态默认目录：`%LOCALAPPDATA%\ldvh`；
4. macOS / Linux 配置默认目录：`~/.ldvh`；
5. Windows 兼容兜底：`%USERPROFILE%\.ldvh`，仅作为兼容识别，不作为首选。

## 配置文件候选

后续可评估以下文件，但本文不创建：

1. `LDVH_USER_HOME/config.yaml`：用户级默认值，例如默认 LDVH root、默认工作区根目录、活动 profile、配置搜索根；
2. `LDVH_USER_HOME/governed-projects.yaml`：用户本机管辖项目登记候选，字段应尽量复用或兼容 `LDVH-GOVERNED-PROJECTS.yaml`；是否允许它承载主登记仍需后续确认；
3. `LDVH_USER_HOME/cache/`：缓存目录，不作为事实源；
4. `LDVH_USER_HOME/state/` 或 `LDVH_USER_HOME/receipts/`：仅在后续 receipt 存储策略重新通过 Human Gate 后才可考虑。

## 解析优先级候选

初步建议：

1. 显式参数 `--config`、`--governance-root` 或等价环境输入；
2. 当前 repo / workspace 或上级目录中的 `LDVH-GOVERNED-PROJECTS.yaml`；
3. 用户级 `LDVH_USER_HOME/governed-projects.yaml`；
4. 未命中时 no-op / unknown。

该顺序的价值是：共享、可审核、可提交的 repo 配置优先；用户配置作为本机兜底和跨项目便利层，不静默覆盖 repo 事实源。

## 后续转入 Spark 的内容

本文已转入 `ldvh-base/sparks/spark-0041-user-local-ldvh-config-directory.yaml`。该 Spark 至少继续跟踪以下问题：

1. 是否正式引入 `LDVH_USER_HOME` 逻辑目录；
2. Windows、macOS、Linux 的默认目录是否按本文候选执行；
3. `LDVH_HOME` 环境变量是否作为最高优先级入口；
4. 配置生成入口是否必须提供“工作区根目录 / 用户级 LDVH 配置目录 / 当前项目根目录”三选项，并默认推荐工作区根目录；
5. 工作区根目录默认是否固定为 LDVH 安装目录的上一级目录，还是允许安装器另行指定；
6. 用户级目录保存主登记，还是只保存默认工作区指针和个人默认值；
7. 用户级 `governed-projects.yaml` 是否复用 10.Att.01 字段，还是建立独立字段表；
8. repo / workspace 配置与用户配置冲突时，是阻断、告警还是 workspace 优先；
9. Code resolver 是否需要新增用户级 fallback 或 workspace pointer 发现；
10. tests 是否覆盖三选项、默认推荐、workspace pointer、Windows 路径、环境变量覆盖和冲突诊断；
11. 是否需要更新 `specs/10-安装与配置规范.md` 与 `10.Att.01`；
12. 是否需要 Web 展示配置来源，且不得把用户级配置写成 Web 主数据源；
13. 用户级配置写入、workspace 配置生成和当前项目根配置生成是否都必须进入 Human Gate。

## 当前不做事项

1. 不修改 `specs/10-安装与配置规范.md`；
2. 不修改 `specs/attachments/10.Att.01-管辖项目配置字段表.md`；
3. 不修改 `code/ldvh_specs.py` 的配置发现逻辑；
4. 不新增 `~/.ldvh`、`%APPDATA%\ldvh` 或其它真实用户目录；
5. 不移动现有 `LDVH-GOVERNED-PROJECTS.yaml`；
6. 不新增配置生成 CLI、安装器交互或 Web 选择界面；
7. 不把本文继续作为 Spark、WorkCase、ADR 或正式规范结论；正式后续以 `spark-0041` 和后续 WorkCase / ADR / specs 变更为准。

## 进入正式工作的条件

后续若要推进，至少需要：

1. Human 确认用户级配置目录进入正式设计；
2. 已转入 `spark-0041`；若继续推进，应从该 Spark 进入 WorkCase 或 ADR，明确目标、边界和验收；
3. 更新 specs 前先确认是否属于 10 的待补齐事项；
4. Code/tests 变更与规范变更同步；
5. 确认不让用户级配置绕过 repo 事实源、Human Gate 或 Hook 安装授权。
