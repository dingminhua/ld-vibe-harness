# LDVH Thin Reference Template

文件状态：thin reference template。本文是 V3 面向无 Hook 或只支持 repo instruction / agent instruction 的环境薄引用模板；本文不是规则源、不是安装记录、不是环境接入状态证明。

## 使用方式

把模板中的 `<LDVH_ROOT>` 替换为当前机器上 LDVH V3 根目录的真实绝对路径后，再交由 Human 按目标环境规则放入 repo instruction、agent instruction 或等价可读入口。

```markdown
#### LDVH V3 thin reference start

Read first:

<LDVH_ROOT>/hooks/LDVH-RUNTIME-PROTOCOL.md

Then read the V3 authority and runtime boundary files in this order:

1. <LDVH_ROOT>/specs/01-保障与衔接.md
2. <LDVH_ROOT>/specs/attachments/01.Att.01-保障消费时机表.md
3. <LDVH_ROOT>/specs/attachments/01.Att.03-环境入口类型表.md
4. <LDVH_ROOT>/specs/attachments/01.Att.05-runtime-payload字段表.md
5. <LDVH_ROOT>/specs/10-管辖项目配置规范.md
6. <LDVH_ROOT>/specs/30-LDVH安装初始化管辖项目配置行动模板.md

After reading, follow the V3 specs and their authorized attachments as the authority.

On context compaction, resume, or thread restore, reread the Runtime Protocol entry before continuing.

#### LDVH V3 thin reference end
```

## 边界

本文只承载入口、读取顺序和回到 V3 specs 的要求。本文不复制 specs 规则，不恢复 `rules/` 目录或 Rules registry，不声明任何环境已经 integrated。
