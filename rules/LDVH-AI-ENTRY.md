# LDVH AI 兼容入口

> 文件性质：历史兼容 Rules 入口资产，不是 specs 正式规范或最终事实源
> 规范来源：`specs/01-目录说明.md`、`specs/04.02-LDVH能力资产与落地保障规范.md`、`specs/04.03-环境入口适配与部署规范.md`
> 适用范围：旧薄入口仍指向 `rules/LDVH-AI-ENTRY.md` 时的兼容转向

---
## 1. 这个文件是什么

这个文件保留给旧环境入口、旧项目说明或旧上下文恢复使用。LDVH 当前推荐使用双入口：

| 入口 | 适用场景 |
|---|---|
| `rules/LDVH-WORKSPACE-ENTRY.md` | 工作区级入口、管辖项目识别、管辖项目 `ldvh-base/` 工作对象、LDVH dogfood 管辖判断 |
| `rules/LDVH-MAINTAINER-ENTRY.md` | LDVH 源码仓库项目级入口、LDVH 产品资产维护、`specs/`、`rules/`、`skills/`、`agents/`、`hooks/`、`code/`、`tests/`、`web/` |

本文件不是最终事实源。正式规则以 `specs/` 为准，管辖项目清单以工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 为准，环境入口适配、部署和检查方法以 `specs/04.03-环境入口适配与部署规范.md` 为准。

---
## 2. 转向规则

AI 读到本文件后，应先判断当前任务入口：

1. 如果当前任务来自工作区级 AGENTS、用户安装 LDVH、管辖项目识别、管辖项目工作对象或 `ldvh-base/` 处理，转入 `rules/LDVH-WORKSPACE-ENTRY.md`；
2. 如果当前任务来自 `ld-vibe-harness` 仓库项目级 AGENTS，或目标是维护 LDVH 产品资产，转入 `rules/LDVH-MAINTAINER-ENTRY.md`；
3. 如果无法判断，应读取工作区根目录 `LDVH-GOVERNED-PROJECTS.yaml` 和当前目录，说明判断依据；仍无法判断时暂停请求 Human 确认。

`ldvh-base/` 始终按被管辖项目的工作对象事实源处理。即使它位于 LDVH 源码仓库内，也应通过工作区入口和管辖项目配置判断后处理。

---
## 3. 薄入口边界

环境入口、项目规则、工作区配置或会话提示只应通过薄引用措施指向入口文件，不应复制本文正文或 specs 正文。薄引用正文只应包含入口指向、压缩或恢复后的重读提示，以及 LDVH 管理段开始和结束标记。

LDVH 不默认自动写入用户环境入口。AI 可以生成可复制的 Codex 薄入口文本，并说明应由用户自行加入环境规则入口。只有在 Human 明确授权、目标入口已定位、已有内容已保护且影响范围已说明时，才可执行受控写入。

---
## 4. STOP 点

出现以下情况时，AI 应暂停并说明需要 Human 确认：

1. 要删除、移动或重命名本兼容入口或两个新入口；
2. 要修改工作区级入口、环境入口、项目规则或等价配置；
3. 要把旧单入口模型恢复为唯一入口；
4. 要把 LDVH 项目级维护入口用于默认处理管辖项目工作对象；
5. 入口内容与 specs 正式规范、管辖项目配置、工作对象事实或 Code 校验结果冲突。

---
## 5. 维护规则

修改本文后，应检查：

1. `rules/LDVH-WORKSPACE-ENTRY.md`；
2. `rules/LDVH-MAINTAINER-ENTRY.md`；
3. `specs/01-目录说明.md`；
4. `specs/04.02-LDVH能力资产与落地保障规范.md`；
5. `specs/04.03-环境入口适配与部署规范.md`；
6. 已授权的工作区级或项目级薄入口。
