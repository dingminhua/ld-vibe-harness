# Tasks

- [x] Task 1: 更新 `specs/11-LDVH-AI协作规范.md`
  - [x] SubTask 1.1: 新增“规范判断必须回原文”通用要求
  - [x] SubTask 1.2: 新增“错误模式转检查项”要求
  - [x] SubTask 1.3: 在机制落地或检查要求中说明 Rules / Skill / Agent 运行时入口不是稳定事实源

- [x] Task 2: 更新 `specs/11.01-Rules机制规范.md`
  - [x] SubTask 2.1: 新增“重要规则回流 specs”要求
  - [x] SubTask 2.2: 明确 Rules 只能保留入口摘要、压缩保护、场景触发或项目专属硬约束，不得长期承载框架级原则正文
  - [x] SubTask 2.3: 将“Rules 审计从 specs 反向发现需求”的原则与“规则回流 specs”衔接

- [x] Task 3: 更新 `specs/11.02-Skill机制规范.md`
  - [x] SubTask 3.1: 新增 LDVH 通用 Skill 部署判断检查流程
  - [x] SubTask 3.2: 明确判断 Skill 可调用性时必须同时检查部署边界、工作区顶层 `.trae/skills/`、YAML `name`、文件结构和 Human Gate
  - [x] SubTask 3.3: 明确不能只凭项目内 `.trae/skills/` 目录或聊天记忆判断 Skill 已落地

- [x] Task 4: 更新 `specs/evals/17-LDVH-Gstack-Trae融合产品方向共识.md`
  - [x] SubTask 4.1: 标记“规范判断回原文”和“重要规则回流 specs”已回流 11 系列正式规范
  - [x] SubTask 4.2: 保留 evals/17 作为入口文档，但不让其替代正式规范

- [x] Task 5: 验证文档一致性
  - [x] SubTask 5.1: 检查 11、11.01、11.02 的新增内容没有互相重复维护跨机制选择表
  - [x] SubTask 5.2: 运行 specs 文档规范相关测试或检查命令

# Task Dependencies

- Task 1、Task 2、Task 3 可并行
- Task 4 依赖 Task 1、Task 2、Task 3
- Task 5 依赖 Task 1-4
