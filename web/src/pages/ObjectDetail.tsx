import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronRight, FileText, Code2, ExternalLink, Link2 } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import StatusBadge from '@/components/StatusBadge';
import { fetchObjectDetail, type ObjectDetail } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import { CATEGORY_COLORS, getCategoryLocale } from '@/utils/categoryColors';

/** 字段分组定义 */
const META_KEYS = ['id', 'type', 'status', 'created', 'updated', 'closed_at', 'title', 'title_en', 'title_zh'];
/** 长文本字段（用 Markdown 渲染） */
const MARKDOWN_FIELDS = ['description', 'success_criteria', 'constraints', 'acceptance', 'verification', 'notes', 'rationale', 'context', 'consequences', 'observation', 'analysis', 'mitigation', 'resolution'];
/** 列表字段（用带图标的条目展示） */
const CHECKLIST_FIELDS = ['acceptance', 'blocked_by'];
/** 引用字段（渲染为可点击的引用列表） */
const REFERENCE_FIELDS = ['related_tasks', 'related_adrs', 'blocked_by', 'source_intent', 'parent_task'];

/** 对象类型中英映射 */
const TYPE_LOCALES: Record<string, { zh: string; en: string }> = {
  intent: { zh: '意图', en: 'Intent' },
  task: { zh: '任务', en: 'Task' },
  adr: { zh: 'ADR', en: 'ADR' },
  pitfall: { zh: 'BUG', en: 'Bug' },
  memo: { zh: '备忘', en: 'Memo' },
  profile: { zh: '画像', en: 'Profile' },
  change: { zh: '变更', en: 'Change' },
};

/** 字段名中英映射 */
const FIELD_LABEL_LOCALES: Record<string, { zh: string; en: string }> = {
  description: { zh: '描述', en: 'Description' },
  success_criteria: { zh: '成功标准', en: 'Success Criteria' },
  constraints: { zh: '约束', en: 'Constraints' },
  acceptance: { zh: '验收标准', en: 'Acceptance' },
  verification: { zh: '验证方式', en: 'Verification' },
  notes: { zh: '备注', en: 'Notes' },
  rationale: { zh: '理由', en: 'Rationale' },
  context: { zh: '背景', en: 'Context' },
  consequences: { zh: '影响', en: 'Consequences' },
  observation: { zh: '观察', en: 'Observation' },
  analysis: { zh: '分析', en: 'Analysis' },
  mitigation: { zh: '缓解措施', en: 'Mitigation' },
  resolution: { zh: '解决方案', en: 'Resolution' },
  blocked_by: { zh: '前置依赖', en: 'Blocked By' },
  source_intent: { zh: '来源意图', en: 'Source Intent' },
  parent_task: { zh: '父任务', en: 'Parent Task' },
  closure_evidence: { zh: '关闭证据', en: 'Closure Evidence' },
  transition_reasons: { zh: '流转记录', en: 'Transition Reasons' },
  options: { zh: '选项', en: 'Options' },
  decision: { zh: '决策', en: 'Decision' },
  related_tasks: { zh: '关联任务', en: 'Related Tasks' },
  related_adrs: { zh: '关联 ADR', en: 'Related ADRs' },
  scope: { zh: '范围', en: 'Scope' },
  impact: { zh: '影响范围', en: 'Impact' },
  severity: { zh: '严重程度', en: 'Severity' },
  category: { zh: '分类', en: 'Category' },
  tags: { zh: '标签', en: 'Tags' },
  path: { zh: '路径', en: 'Path' },
  changes: { zh: '变更列表', en: 'Changes' },
  related_docs: { zh: '关联文档', en: 'Related Docs' },
};

export default function ObjectDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const { t, getStatus, locale } = useI18n();

  useEffect(() => {
    if (!type || !id) return;
    fetchObjectDetail(type, id)
      .then(setDetail)
      .catch((e) => setError(e.message));
  }, [type, id]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  const obj = detail.data;
  const objId = detail.summary.id;
  const objType = detail.summary.type;
  const objStatus = detail.summary.status;
  const typeColor = CATEGORY_COLORS[objType] || CATEGORY_COLORS.other;

  const displayTitle = (locale === 'en'
    ? ((obj.title_en as string) || obj.title as string)
    : ((obj.title_zh as string) || obj.title as string)) || objId;

  // 内容字段（排除元信息）
  const contentEntries = Object.entries(obj).filter(
    ([key]) => !META_KEYS.includes(key)
  );

  // 生成真正的 YAML 源码
  const yamlSource = objectToYaml(obj);

  return (
    <div className="mx-auto max-w-4xl p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/objects/${type}`)}
          className="mb-3 flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
        >
          <ArrowLeft size={14} />
          {t('objectDetail.back')}
        </button>
        <div className="flex items-start gap-3">
          <span
            className="mt-1 shrink-0 rounded px-2 py-0.5 text-xs font-medium"
            style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
          >
            {TYPE_LOCALES[objType] ? (locale === 'en' ? TYPE_LOCALES[objType].en : TYPE_LOCALES[objType].zh) : objType}
          </span>
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-semibold text-ldvh-text-primary">{displayTitle}</h1>
            <p className="mt-0.5 font-mono text-xs text-ldvh-text-secondary">{objId}</p>
          </div>
          <StatusBadge status={objStatus} statusLabel={getStatus(objStatus)} size="md" />
        </div>
      </div>

      {/* Metadata row */}
      <div className="mb-6 flex flex-wrap gap-2">
        <MetaChip label={t('objectDetail.created')} value={obj.created as string || '-'} />
        <MetaChip label={t('objectDetail.updated')} value={obj.updated as string || '-'} />
        {obj.closed_at && <MetaChip label={t('objectDetail.closedAt')} value={obj.closed_at as string} />}
      </div>

      {/* Content fields */}
      <div className="mb-6 flex flex-col gap-5">
        {contentEntries.map(([key, value]) => (
          <ContentField key={key} fieldKey={key} value={value} locale={locale} />
        ))}
      </div>

      {/* YAML source */}
      <div className="rounded-lg border border-ldvh-border bg-ldvh-panel overflow-hidden">
        <button
          onClick={() => setShowYaml(!showYaml)}
          className="flex w-full items-center gap-2 p-3 text-sm text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary"
        >
          <Code2 size={14} />
          <span>{t('objectDetail.yamlSource')}</span>
          <span className="ml-auto">{showYaml ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
        </button>
        {showYaml && (
          <div className="border-t border-ldvh-border">
            <SyntaxHighlighter
              language="yaml"
              style={oneDark}
              customStyle={{ margin: 0, borderRadius: 0, fontSize: '12px', maxHeight: '400px' }}
              showLineNumbers
            >
              {yamlSource}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    </div>
  );
}

/** 元信息小标签 */
function MetaChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5 rounded-md border border-ldvh-border bg-ldvh-panel px-2.5 py-1">
      <span className="text-[10px] text-ldvh-text-secondary">{label}</span>
      <span className="font-mono text-xs text-ldvh-text-primary">{value}</span>
    </div>
  );
}

/** 内容字段：根据字段类型选择渲染方式 */
function ContentField({ fieldKey, value, locale }: { fieldKey: string; value: unknown; locale: string }) {
  if (value === null || value === undefined) return null;
  if (value === '') return null;

  // 字段名国际化
  const labelEntry = FIELD_LABEL_LOCALES[fieldKey];
  const label = labelEntry
    ? (locale === 'en' ? labelEntry.en : labelEntry.zh)
    : fieldKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <div className="mb-2 flex items-center gap-2">
        <FileText size={13} className="text-ldvh-accent" />
        <h4 className="text-xs font-medium tracking-wide text-ldvh-text-secondary">{label}</h4>
      </div>
      <FieldValue fieldKey={fieldKey} value={value} depth={0} locale={locale} />
    </div>
  );
}

/** 递归渲染字段值 */
function FieldValue({ fieldKey, value, depth, locale }: { fieldKey: string; value: unknown; depth: number; locale: string }) {
  const { t } = useI18n();
  if (value === null || value === undefined) {
    return <span className="text-xs text-ldvh-text-secondary italic">{t('common.null')}</span>;
  }

  // 字符串
  if (typeof value === 'string') {
    // 空字符串不显示
    if (value === '') return null;

    // 检查列表字段（Markdown 格式的 checklist）
    if (CHECKLIST_FIELDS.includes(fieldKey) && value.includes('- [')) {
      return (
        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1">
          <Markdown remarkPlugins={[remarkGfm]}>{value}</Markdown>
        </div>
      );
    }

    // Markdown 字段
    if (MARKDOWN_FIELDS.includes(fieldKey)) {
      return (
        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1 prose-pre:my-2 prose-code:text-ldvh-accent">
          <Markdown remarkPlugins={[remarkGfm]}>{value}</Markdown>
        </div>
      );
    }

    // 长文本（含换行）
    if (value.includes('\n') || value.length > 200) {
      return (
        <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-pre:my-2">
          <Markdown remarkPlugins={[remarkGfm]}>{value}</Markdown>
        </div>
      );
    }

    // 单字符串引用字段（source_intent、parent_task）
    if (REFERENCE_FIELDS.includes(fieldKey) && parseRefType(value)) {
      return <ReferenceLink refId={value} />;
    }

    // 短文本
    return <span className="text-sm text-ldvh-text-primary">{value}</span>;
  }

  // 布尔值
  if (typeof value === 'boolean') {
    return (
      <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${value ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
        {value ? t('common.true') : t('common.false')}
      </span>
    );
  }

  // 数字
  if (typeof value === 'number') {
    return <span className="font-mono text-sm text-ldvh-accent">{value}</span>;
  }

  // 数组
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-xs text-ldvh-text-secondary italic">{t('common.empty')}</span>;
    }

    // 字符串数组
    if (typeof value[0] === 'string') {
      // related_docs 字段渲染为可折叠展开的文档卡片
      if (fieldKey === 'related_docs') {
        return <RelatedDocsList docs={value as string[]} />;
      }
      // 引用字段渲染为可点击的引用列表
      if (REFERENCE_FIELDS.includes(fieldKey)) {
        return <ReferenceList refs={value as string[]} />;
      }
      return (
        <div className="flex flex-wrap gap-1.5">
          {value.map((item, i) => (
            <span key={i} className="rounded-md bg-ldvh-bg px-2 py-0.5 text-xs text-ldvh-text-primary border border-ldvh-border">
              {item}
            </span>
          ))}
        </div>
      );
    }

    // 对象数组
    return (
      <div className="flex flex-col gap-2">
        {value.map((item, i) => (
          <div key={i} className="rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <FieldValue fieldKey={fieldKey} value={item} depth={depth + 1} locale={locale} />
          </div>
        ))}
      </div>
    );
  }

  // 对象
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>);
    return (
      <div className={`flex flex-col gap-2 ${depth > 0 ? '' : ''}`}>
        {entries.map(([k, v]) => {
          const subLabel = FIELD_LABEL_LOCALES[k];
          const displayKey = subLabel
            ? (locale === 'en' ? subLabel.en : subLabel.zh)
            : k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          return (
            <div key={k} className="flex gap-2">
              <span className="shrink-0 rounded bg-ldvh-bg px-1.5 py-0.5 text-[11px] text-ldvh-text-secondary border border-ldvh-border">
                {displayKey}
              </span>
              <div className="min-w-0 flex-1">
                <FieldValue fieldKey={k} value={v} depth={depth + 1} locale={locale} />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return <span className="text-sm text-ldvh-text-primary">{String(value)}</span>;
}

/** 从引用 ID 解析对象类型（如 task-0001 → task） */
function parseRefType(refId: string): string | null {
  const m = refId.match(/^([a-z]+)-\d+$/);
  return m ? m[1] : null;
}

/** 引用链接：单个可点击引用项 */
function ReferenceLink({ refId }: { refId: string }) {
  const navigate = useNavigate();
  const { locale, getStatus } = useI18n();
  const [info, setInfo] = useState<{ title: string; status: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const refType = parseRefType(refId);

  useEffect(() => {
    if (!refType) { setLoading(false); return; }
    fetchObjectDetail(refType, refId)
      .then((detail) => {
        const obj = detail.data;
        const title = (locale === 'en'
          ? (obj.title_en as string || obj.title as string)
          : (obj.title_zh as string || obj.title as string)) || refId;
        setInfo({ title, status: detail.summary.status });
      })
      .catch(() => setInfo(null))
      .finally(() => setLoading(false));
  }, [refType, refId, locale]);

  const typeColor = refType ? (CATEGORY_COLORS[refType] || CATEGORY_COLORS.other) : CATEGORY_COLORS.other;
  const typeLabel = TYPE_LOCALES[refType || '']
    ? (locale === 'en' ? TYPE_LOCALES[refType!].en : TYPE_LOCALES[refType!].zh)
    : refType;

  const handleClick = () => {
    if (refType) navigate(`/objects/${refType}/${refId}`);
  };

  return (
    <button
      onClick={handleClick}
      disabled={!refType}
      className="flex w-full items-center gap-2 rounded-lg border border-ldvh-border bg-ldvh-bg px-3 py-2 text-left text-sm transition-colors hover:bg-ldvh-border/30 disabled:cursor-default"
    >
      <Link2 size={13} className="shrink-0" style={{ color: typeColor }} />
      {typeLabel && (
        <span
          className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
          style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
        >
          {typeLabel}
        </span>
      )}
      <span className="min-w-0 flex-1 truncate text-ldvh-text-primary">
        {loading ? <span className="text-ldvh-text-secondary">{refId}</span> : (info?.title || refId)}
      </span>
      {info?.status && (
        <span className="shrink-0 text-[10px] text-ldvh-text-secondary">{getStatus(info.status)}</span>
      )}
    </button>
  );
}

/** 引用列表：多个引用项，每个独立一行 */
function ReferenceList({ refs }: { refs: string[] }) {
  return (
    <div className="flex flex-col gap-1.5">
      {refs.map((ref, i) => (
        <ReferenceLink key={i} refId={ref} />
      ))}
    </div>
  );
}

/** 关联文档列表：可折叠展开查看内容 */
function RelatedDocsList({ docs }: { docs: string[] }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [docContent, setDocContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const { t, locale } = useI18n();

  const handleToggle = async (idx: number, docPath: string) => {
    if (expandedIdx === idx) {
      setExpandedIdx(null);
      setDocContent(null);
      return;
    }

    // 外部链接直接打开
    if (docPath.startsWith('http')) {
      window.open(docPath, '_blank', 'noopener,noreferrer');
      return;
    }

    setExpandedIdx(idx);
    setDocContent(null);
    setLoadError(null);
    setLoading(true);

    try {
      const res = await fetch(`/api/docs?path=${encodeURIComponent(docPath)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setDocContent(data.content);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      {docs.map((doc, i) => {
        const isExternal = doc.startsWith('http');
        const isExpanded = expandedIdx === i;
        return (
          <div key={i} className="rounded-lg border border-ldvh-border bg-ldvh-bg overflow-hidden">
            <button
              onClick={() => handleToggle(i, doc)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors hover:bg-ldvh-border/30"
            >
              {isExternal ? (
                <ExternalLink size={13} className="shrink-0 text-ldvh-accent" />
              ) : (
                <FileText size={13} className="shrink-0 text-ldvh-accent" />
              )}
              <span className="min-w-0 flex-1 truncate text-ldvh-text-primary">{doc}</span>
              {isExternal ? (
                <span className="shrink-0 text-[10px] text-ldvh-text-secondary">↗</span>
              ) : (
                <span className="shrink-0 text-ldvh-text-secondary">
                  {isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                </span>
              )}
            </button>
            {isExpanded && (
              <div className="border-t border-ldvh-border">
                {loading ? (
                  <div className="flex items-center gap-2 px-3 py-3">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
                    <span className="text-xs text-ldvh-text-secondary">{t('common.loading')}</span>
                  </div>
                ) : loadError ? (
                  <div className="px-3 py-3 text-xs text-red-400">{loadError}</div>
                ) : (
                  <div className="max-h-80 overflow-y-auto px-3 py-3">
                    <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-1 prose-li:my-0.5 prose-ul:my-1 prose-pre:my-2 prose-code:text-ldvh-accent">
                      <Markdown remarkPlugins={[remarkGfm]}>{docContent || ''}</Markdown>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** 简单对象转 YAML 字符串 */
function objectToYaml(obj: Record<string, unknown>, indent: number = 0): string {
  const prefix = '  '.repeat(indent);
  const lines: string[] = [];

  for (const [key, value] of Object.entries(obj)) {
    if (value === null || value === undefined) {
      lines.push(`${prefix}${key}: null`);
    } else if (typeof value === 'string') {
      if (value.includes('\n') || value.includes(':') || value.includes('#') || value.startsWith(' ')) {
        lines.push(`${prefix}${key}: |`);
        for (const line of value.split('\n')) {
          lines.push(`${prefix}  ${line}`);
        }
      } else {
        lines.push(`${prefix}${key}: ${value}`);
      }
    } else if (typeof value === 'boolean' || typeof value === 'number') {
      lines.push(`${prefix}${key}: ${value}`);
    } else if (Array.isArray(value)) {
      lines.push(`${prefix}${key}:`);
      for (const item of value) {
        if (typeof item === 'string') {
          lines.push(`${prefix}- ${item}`);
        } else if (typeof item === 'object' && item !== null) {
          const subLines = objectToYaml(item as Record<string, unknown>, indent + 1);
          lines.push(`${prefix}- ${subLines.trimStart()}`);
        } else {
          lines.push(`${prefix}- ${item}`);
        }
      }
    } else if (typeof value === 'object') {
      lines.push(`${prefix}${key}:`);
      lines.push(objectToYaml(value as Record<string, unknown>, indent + 1));
    }
  }

  return lines.join('\n');
}
