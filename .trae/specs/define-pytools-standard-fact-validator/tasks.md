# Tasks

- [x] Task 1: 实现 `tools/check_fact_model.py` 最小 Fact Validator
  - [x] SubTask 1.1: 定义新工具内部 PyTools 最小标准：Issue 数据结构、severity（error/warning）、exit code（0 通过、1 校验失败、2 输入/解析错误）、统一输出摘要
  - [x] SubTask 1.2: 实现文件/目录输入解析：支持单个 `.yaml` 文件和目录批量校验；目录只扫描 `.yaml` 文件
  - [x] SubTask 1.3: 实现对象类型识别：根据路径或 YAML `type` 识别 Intent、Task、Evidence；无法识别返回 exit code 2
  - [x] SubTask 1.4: 实现 Intent 校验：文件名、id、type、status、必填字段、list 字段类型
  - [x] SubTask 1.5: 实现 Task 校验：文件名、id、type、status、必填字段、list 字段类型、closed 条件必填
  - [x] SubTask 1.6: 实现 Evidence 校验：文件名、id、type、status、必填字段、evidence_type、verification_result、source_task/source_adr 至少一个
  - [x] SubTask 1.7: 确保工具只读，不执行任何写入

- [x] Task 2: 新增 `tests/tools/test_check_fact_model.py`
  - [x] SubTask 2.1: 覆盖合法 Intent / Task / Evidence 样例，期望 exit code 0
  - [x] SubTask 2.2: 覆盖缺少必填字段、非法 status、type 不匹配、文件名非法，期望 exit code 1
  - [x] SubTask 2.3: 覆盖不存在路径、YAML 解析失败、无法识别对象类型，期望 exit code 2
  - [x] SubTask 2.4: 覆盖目录批量校验，期望汇总结果正确

- [x] Task 3: 运行验证命令
  - [x] SubTask 3.1: 运行 `python3 -m pytest tests/tools/test_check_fact_model.py`
  - [x] SubTask 3.2: 运行现有 tools 测试（至少 `python3 -m pytest tests/tools`）确认未破坏旧工具
  - [x] SubTask 3.3: 运行 `python3 tools/check_fact_model.py ldvh-base/intents/ ldvh-base/tasks/ ldvh-base/evidence/`，确认空目录或目录样例处理符合预期

# Task Dependencies

- Task 2 依赖 Task 1
- Task 3 依赖 Task 1 和 Task 2
