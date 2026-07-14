# V4 08 Web 规范与 V3 实践适配审核记录

> 记录性质：本文为 `specs/08-Web 呈现与交互规范.md` 集中审核提供当前实现证据和差异记录，不是规则源，不修改 `web/` 或 `icons/`，也不表示现有 Web 已经符合 V4。

## 1. 审核范围

本轮只读检查：

1. `specs/08-Web 呈现与交互规范.md`；
2. `web/api/` 的事实读取、项目文件、Git 和 Spark 写入入口；
3. `web/src/` 的 App Shell、对象列表与详情、ReadingPanel、复制、i18n 和响应式实现；
4. `web/docs/` 与 `web/design-workspace/` 中的当前产品和设计说明；
5. `web/package.json` 声明的检查与测试入口；
6. `icons/` 和 `web/public/` 中的现有图标资产边界。

本轮不修改 Web 源码、依赖、配置、设计稿、测试或图标，不安装依赖，不生成构建产物，也不恢复归档中的 V3 tests。

## 2. 可以保留的产品价值

| 产品价值 | 当前证据 | V4 保留边界 |
|---|---|---|
| Web 独立服务 Human | `web/api/server.ts`、`web/src/App.tsx` 和各页面直接通过 Web API 组织 Human 视图，没有调用 Helper CLI | 保留 Web 不经过 Helper 的架构关系；共享解析 Code 不能取得页面事实权威 |
| 列表、详情与扩展阅读连接 | `ObjectList.tsx`、`ObjectDetail.tsx`、`ReadingPanel.tsx`、`panelContext.tsx` 及相关页面文档 | 保留从摘要进入同一来源对象的阅读价值；不得保留硬编码事实类型和字段作为 V4 契约 |
| 语义阅读而非只展示原始 YAML | `ObjectDetail.tsx` 已按不同内容组织阅读节点，并把 YAML 保留为兜底；`web/docs/04-ObjectDetail.md` 和 `07-内容可读性深度研究.md` 记录相同方向 | 保留面向 Human 的信息层次和扩展阅读；具体节点、字段和状态必须重新回到 V4 当前来源 |
| 来源路径与复制入口 | `facts.ts` 返回 `source_refs` 和对象路径；`CopyPathButton.tsx`、ProjectFiles 和页面文档区分对象路径、文档路径、URL、引用和 commit | 保留来源导航，并在复制时保留适用的来源信息；复制内容的身份和省略范围仍须由实际来源验证 |
| 中英文界面基础 | `i18n/context.tsx`、`i18n/locales.ts` 及主要页面使用 `useI18n` | 保留 i18n 机制和事实正文不被 UI 翻译覆盖的方向；不能仅凭字典和调用存在声明全部界面已覆盖 |
| 响应式与键盘交互基础 | 页面广泛使用 Tailwind 响应式 class；Layout 和 ReadingPanel 支持部分窄屏变化及 Escape 关闭；按钮具有 `aria-label` 和 focus 样式 | 保留已有实现与设计资产；支持的视口、键盘和辅助技术范围仍须真实测试 |
| 空态、失败与只读工具页 | 页面具有部分 Empty、loading、error 呈现；ProjectFiles 文档和实现明确只读浏览文件、diff 与 history | 保留失败可见和只读工具价值；当前部分 API 路径仍会把读取或解析失败变为空列表、零计数或无问题结果，不能据此声明失败已经完整呈现 |
| 图标与视觉语言 | `icons/`、`web/public/`、`SemanticIcon.tsx` 和设计系统文档形成现有产品资产 | 图标和视觉实现继续保留；它们不定义事实类型、状态或规则语义 |

这些证据只证明相应产品价值已经在 V3 实践中出现，不证明所有页面、对象、语言、视口或交互均已正确实现。

## 3. 必须与 V4 当前来源重新对齐的内容

| 当前实践 | 实际证据 | V4 处置 |
|---|---|---|
| 读取范围与管辖判断未接入 02 | `facts.ts` 固定从单一 `LDVH_ROOT` 和五个目录读取，没有工作对象、管辖项目配置解析或事实资格判断；`projectFiles.ts` 在找不到配置时自行创建 `workspace` 项目，在两处候选配置中取首个存在文件，并未验证 02 的字段闭集、项目唯一性、Git worktree 或 common-dir | 这些入口只能视为 V3 本地读取实现；完成 02 的配置选择、工作对象管辖判定和读取范围验证前，不得作为 V4 项目范围或当前事实读取能力 |
| 五类事实对象硬编码 | `web/api/services/facts.ts` 固定 `workcase/adr/pitfall/spark/study` 与目录；Sidebar、ObjectDetail 和多个 utils 固定相同类型、字段和状态 | 在相应具体事实类型按 active 05 完成准入并具有当前定义来源前，只作为 V3 历史实现；不得声明为 V4 支持类型 |
| V3 字段、状态和规范编号 | ObjectDetail、ObjectList、状态 utilities 和 `web/docs/` 大量直接引用 WorkCase orchestration、V3 状态、20–24 编号及已退出规范路径 | 实现适配时按新的具体来源逐项重建数据契约；不建立兼容义务，也不让 Web 文档成为字段或状态来源 |
| 读取失败与派生范围被隐藏 | `facts.ts` 在 YAML 或 Markdown 解析失败时返回 `null` 并过滤对象，成功结果仍固定 `issues: []`；Dashboard 还会把部分失败变成空数组、零计数，并且统计没有观察时间、来源版本或遗漏范围 | 解析失败和遗漏必须进入实际结果；观察时间、来源范围和过期判断成立前，不得把当前列表、计数或 Dashboard 聚合作为完整当前事实或可靠派生能力 |
| Spark 直接写入仍可调用 | `web/api/routes/sparks.ts` 直接定义字段白名单、`pending`、ID、目录和写后验证，并引用 V3 08/20；路由仍挂载在 `app.ts`，ObjectList 仍呈现 `SparkCreate`；文件写入后的读取或字段验证失败会留下文件，但响应没有报告该残留变化 | “没有 V4 权威”不表示入口已经隔离。在 Spark 成为 V4 事实类型、写入契约和相应 Code 能力成立并能报告部分结果与回读差异前，任何 V4 Web 运行或部署都必须隔离该写入口 |
| Web 内部解析承担领域判断 | `facts.ts`、对象页面和 utilities 直接解析字段、状态、关系与摘要 | 未来可以复用共享 Schema 和纯解析能力，但语义必须来自正式来源；DTO、组件和 parser 不得形成第二权威 |
| 文件读取范围存在逃逸 | Docs API 先用裸字符串前缀判断允许目录，再解析路径，`specs/../...` 可越过允许目录；ProjectFiles 只用词法路径判断项目内范围，项目内 symlink 仍可能指向项目外；当前 API 没有认证保护 | 修正真实路径与允许目录边界前，不得把这些入口作为 V4 有边界读取能力；未建立认证和部署范围前，不得扩展到远程或多用户暴露 |
| 移动端主导航缺口 | `Layout.tsx` 在小于 `sm` 时隐藏 Sidebar；当前文件没有移动主导航替代入口，而设计资料分别提出底部抽屉、移动导航补位等方向 | 保留现有设计探索；在唯一实现方向和真实测试成立前，不声明移动导航已确认或可用 |
| 设计资料中的支持结论 | 设计系统文档记录对比度、WCAG 目标、响应式断点和组件契约，页面文档也使用“已确认”“可实现”等历史判断 | 继续作为设计输入；无当前测试和 V4 来源对齐时，不得改写为已符合、已验证或完整支持 |
| 认证与远程入口占位 | `web/api/routes/auth.ts` 的 register/login/logout 返回 501 | 保持未实现；08 不提前建立认证、远程多用户或权限系统契约 |

## 4. 只属于实现的资产

以下内容可以继续作为产品实现资产，但不进入 08 的稳定规则正文：

1. React、Express、Vite、Tailwind、Zustand、Lucide、js-yaml 等技术选择；
2. App Shell 的具体宽度、断点、CSS class、颜色 token 和组件树；
3. 当前路由、API 路径、DTO、hooks、utils 和页面文件划分；
4. V3 的五个对象模块、Dashboard 卡片、Changelog parser 和 ProjectFiles 布局；
5. `icons/` 的具体 PNG 尺寸、文件名和前端引用位置；
6. `web/design-workspace/` 中的截图、HTML 探索和候选设计。

这些资产是否继续使用，由后续具体 Web 实现规划和差异审核决定；08 不要求为了 V4 形式统一而重写，也不允许它们反向定义 V4 领域语义。

## 5. 当前验证结果与限制

本轮尝试执行 `web/package.json` 已声明的三个只读入口：

| 入口 | 实际结果 | 可得结论 |
|---|---|---|
| `npm run check` | 退出 127，当前未安装 `tsc` | 未执行 TypeScript 检查，不得声明通过或失败 |
| `npm run lint` | 退出 127，当前未安装 `eslint` | 未执行 lint，不得声明通过或失败 |
| `npm run test:web:api` | 退出 127，当前未安装 `tsx`；当前工作树也没有脚本引用的 `tests/web/api/*.test.ts` | V3 测试入口当前不可执行，不能用 package script 或 Web 测试文档证明 API 已验证 |

当前只证明：Web 源码、设计资料和 npm scripts 仍存在，且本轮能够进行静态只读审核。没有依赖安装结果、构建结果、API tests、页面 tests、E2E、可访问性、响应式或真实浏览器验证依据。

观察日 2026-07-12，[W3C WAI 的 WCAG 2 概览](https://www.w3.org/WAI/standards-guidelines/wcag/)说明 WCAG 2.0、2.1 和 2.2 都是已发布标准，WCAG 2.2 是 W3C 鼓励采用的最新 WCAG 2 版本，WCAG 3 仍是早期草案。该一手资料只支持把 WCAG 2.2 作为后续可访问性要求的候选参考；08 没有据此写入全局符合等级，当前 Web 也没有取得 WCAG 符合性声明。

## 6. 对 08 的判断

08 已经正确覆盖：

1. Web 直接服务 Human、独立读取且不经过 Helper；
2. 工作对象和读取范围；
3. Working Tree 当前内容、显式历史和来源回指；
4. 派生内容、观察时间、遗漏范围和过期；
5. 来源、未知范围、导航、复制和支持范围内可识别性；
6. 默认只读、受控操作前置、写后回读和 Human 决定证明边界；
7. V3 产品价值、领域契约、实现资产和未验证声明的分流；
8. Web 实现与支持声明仍需范围匹配测试。

本轮没有发现需要把 V3 具体页面、五类事实对象、Spark 写入、移动导航方案、测试目录或技术栈写入 08 正文的理由。上述内容留在本记录和现有 Web 资产中，避免 08 成为当前实现快照或第二领域来源。现有产品价值可以继续作为适配输入，但读取范围、失败隐藏、派生信息缺口、仍可调用的直接写入和文件读取逃逸都属于 V4 运行或部署前必须处理的实现差异。

修正后的独立架构边界和术语复核均为 0 blocker、0 major、0 minor。08 已转为 `active`；这只表示 Web 的通用呈现与交互边界完成审核，不表示现有 `web/` 已符合 V4。后续修改 Web 前仍须为准备消费的具体来源、数据契约和实现范围形成 Code 实现规划，并取得实际可执行的 Web 测试证据。
