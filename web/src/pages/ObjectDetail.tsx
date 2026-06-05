import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronRight, FileText, Code2, Info, Pencil } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import StatusBadge from '@/components/StatusBadge';
import ChecklistCard from '@/components/ChecklistCard';
import ReferenceCard from '@/components/ReferenceCard';
import SummaryText from '@/components/SummaryText';
import DocPreviewLink from '@/components/DocPreviewLink';
import EvidenceBlock from '@/components/EvidenceBlock';
import ReadingPanel, { type PanelContent } from '@/components/ReadingPanel';
import IntentSelector from '@/components/IntentSelector';
import { fetchObjectDetail, patchObjectField, type ObjectDetail } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import { getTypeDescription, getStatusHint } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';

/** 字段分组定义 */
const META_KEYS = ['id', 'type', 'status', 'created', 'updated', 'closed_at', 'title', 'title_en', 'title_zh', 'aggregated_deliverables', 'aggregated_docs'];
/** 长文本字段（用 SummaryText 组件渲染，支持展开/收起） */
const SUMMARY_TEXT_FIELDS = ['description', 'context', 'consequences', 'success_criteria', 'constraints', 'rationale', 'observation', 'analysis', 'mitigation', 'resolution', 'verification', 'notes'];
/** 引用字段（用 ReferenceCard 组件渲染） */
const REFERENCE_FIELDS = ['blocked_by', 'source_intent', 'parent_task', 'related_tasks', 'related_adrs'];
/** 可折叠的关联内容字段（intent 类型默认展开，其他类型默认折叠） */
const COLLAPSIBLE_FIELDS = ['related_tasks', 'related_docs', 'related_adrs', 'deliverables', 'blocked_by'];
/** Task 类型字段展示优先顺序 */
const TASK_FIELD_ORDER = ['acceptance', 'blocked_by', 'related_docs', 'deliverables'];

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
  deliverables: { zh: '产出物', en: 'Deliverables' },
};

export default function ObjectDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelContent, setPanelContent] = useState<PanelContent | null>(null);
  const { t, getStatus, locale } = useI18n();

  const openDocPanel = useCallback((path: string) => {
    setPanelContent({ type: 'doc', path });
    setPanelOpen(true);
  }, []);

  const openRefPanel = useCallback((refType: string, refId: string) => {
    setPanelContent({ type: 'object', refType, refId });
    setPanelOpen(true);
  }, []);

  const closePanel = useCallback(() => {
    setPanelOpen(false);
  }, []);

  // Listen for ldvh:doc-preview and ldvh:ref-preview custom events
  useEffect(() => {
    const handleDocPreview = (e: Event) => {
      const customEvent = e as CustomEvent<{ path: string }>;
      openDocPanel(customEvent.detail.path);
    };

    const handleRefPreview = (e: Event) => {
      const customEvent = e as CustomEvent<{ refType: string; refId: string }>;
      // On desktop, prevent navigation and open panel instead
      if (window.innerWidth >= 1024) {
        e.preventDefault();
        openRefPanel(customEvent.detail.refType, customEvent.detail.refId);
      }
    };

    document.addEventListener('ldvh:doc-preview', handleDocPreview);
    document.addEventListener('ldvh:ref-preview', handleRefPreview);
    return () => {
      document.removeEventListener('ldvh:doc-preview', handleDocPreview);
      document.removeEventListener('ldvh:ref-preview', handleRefPreview);
    };
  }, [openDocPanel, openRefPanel]);

  const refreshDetail = useCallback(() => {
    if (!type || !id) return;
    fetchObjectDetail(type, id)
      .then(setDetail)
      .catch((e) => setError(e.message));
  }, [type, id]);

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
  const typeDesc = getTypeDescription(objType, locale);
  const statusHint = getStatusHint(objStatus, locale);

  const displayTitle = (locale === 'en'
    ? ((obj.title_en as string) || obj.title as string)
    : ((obj.title_zh as string) || obj.title as string)) || objId;

  // 聚合字段（仅 Intent 类型使用）
  const aggregatedDeliverables = (obj.aggregated_deliverables as string[]) || [];
  const aggregatedDocs = (obj.aggregated_docs as string[]) || [];
  const hasAggregatedDeliverables = aggregatedDeliverables.length > 0;
  const hasAggregatedDocs = aggregatedDocs.length > 0;

  // 内容字段（排除元信息）
  const contentEntries = Object.entries(obj).filter(
    ([key]) => !META_KEYS.includes(key)
  );

  // Task 类型字段排序：acceptance → blocked_by → related_docs → 其余按原顺序
  if (objType === 'task') {
    contentEntries.sort((a, b) => {
      const aIdx = TASK_FIELD_ORDER.indexOf(a[0]);
      const bIdx = TASK_FIELD_ORDER.indexOf(b[0]);
      if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
      if (aIdx !== -1) return -1;
      if (bIdx !== -1) return 1;
      return 0;
    });
  }

  // 生成真正的 YAML 源码
  const yamlSource = objectToYaml(obj);

  return (
    <div className="flex h-full">
      {/* Main content area */}
      <div className={`flex-1 overflow-y-auto transition-all duration-300 ${panelOpen ? 'lg:mr-0' : ''}`}>
        <div className={`mx-auto p-6 ${panelOpen ? 'max-w-4xl' : 'max-w-4xl'}`}>
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
                {typeDesc && (
                  <p className="mt-1 text-xs text-ldvh-text-secondary">{typeDesc}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1.5">
                <StatusBadge status={objStatus} statusLabel={getStatus(objStatus)} size="md" />
                {statusHint && (
                  <span className="text-[11px] text-ldvh-text-secondary">{statusHint}</span>
                )}
              </div>
            </div>
            {objStatus === 'review_needed' && (
              <div className="mt-3 flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                <Info size={14} className="shrink-0 text-amber-400" />
                <span className="text-xs text-amber-300">{t('objectDetail.humanGateTip')}</span>
              </div>
            )}
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
              <ContentField key={key} fieldKey={key} value={value} locale={locale} objType={objType} objId={objId} onRefresh={refreshDetail} />
            ))}
          </div>

          {/* 聚合区域 - 仅 Intent 类型显示 */}
          {objType === 'intent' && (hasAggregatedDeliverables || hasAggregatedDocs) && (
            <div className="mb-6 flex flex-col gap-5">
              {hasAggregatedDeliverables && (
                <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <FileText size={13} className="text-ldvh-accent" />
                    <h4 className="text-xs font-medium tracking-wide text-ldvh-text-secondary">
                      {t('objectDetail.aggregatedDeliverables')}
                    </h4>
                  </div>
                  <DocPreviewLink docs={aggregatedDeliverables} />
                </div>
              )}
              {hasAggregatedDocs && (
                <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <FileText size={13} className="text-ldvh-accent" />
                    <h4 className="text-xs font-medium tracking-wide text-ldvh-text-secondary">
                      {t('objectDetail.aggregatedDocs')}
                    </h4>
                  </div>
                  <DocPreviewLink docs={aggregatedDocs} />
                </div>
              )}
            </div>
          )}

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
      </div>

      {/* Right reading panel */}
      <ReadingPanel open={panelOpen} onClose={closePanel} content={panelContent} />
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
function ContentField({ fieldKey, value, locale, objType, objId, onRefresh }: { fieldKey: string; value: unknown; locale: string; objType: string; objId: string; onRefresh: () => void }) {
  const isCollapsible = COLLAPSIBLE_FIELDS.includes(fieldKey);
  const [collapsed, setCollapsed] = useState(isCollapsible ? objType !== 'intent' : false);

  if (value === null || value === undefined) return null;
  if (value === '') return null;

  // 字段名国际化
  const labelEntry = FIELD_LABEL_LOCALES[fieldKey];
  const label = labelEntry
    ? (locale === 'en' ? labelEntry.en : labelEntry.zh)
    : fieldKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
      <div
        className={`mb-2 flex items-center gap-2 ${isCollapsible ? 'cursor-pointer select-none focus:outline-none' : ''}`}
        onClick={isCollapsible ? () => setCollapsed(c => !c) : undefined}
      >
        <FileText size={13} className="text-ldvh-accent" />
        <h4 className="text-xs font-medium tracking-wide text-ldvh-text-secondary">{label}</h4>
        {isCollapsible && (
          <span className="ml-auto text-ldvh-text-secondary">
            {collapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
          </span>
        )}
      </div>
      {!collapsed && <FieldValue fieldKey={fieldKey} value={value} depth={0} locale={locale} objType={objType} objId={objId} onRefresh={onRefresh} />}
    </div>
  );
}

/** 递归渲染字段值 */
function FieldValue({ fieldKey, value, depth, locale, objType, objId, onRefresh }: { fieldKey: string; value: unknown; depth: number; locale: string; objType?: string; objId?: string; onRefresh?: () => void }) {
  const { t } = useI18n();
  const [editingSourceIntent, setEditingSourceIntent] = useState(false);
  const [saving, setSaving] = useState(false);
  if (value === null || value === undefined) {
    return <span className="text-xs text-ldvh-text-secondary italic">{t('common.null')}</span>;
  }

  // 字符串
  if (typeof value === 'string') {
    // 空字符串不显示
    if (value === '') return null;

    // acceptance 字段使用 ChecklistCard 组件
    if (fieldKey === 'acceptance') {
      return <ChecklistCard value={value} />;
    }

    // closure_evidence 字段使用 EvidenceBlock 组件
    if (fieldKey === 'closure_evidence') {
      return <EvidenceBlock value={value} />;
    }

    // 长文本字段使用 SummaryText 组件
    if (SUMMARY_TEXT_FIELDS.includes(fieldKey)) {
      return <SummaryText value={value} />;
    }

    // 单字符串引用字段（source_intent、parent_task）使用 ReferenceCard
    if (REFERENCE_FIELDS.includes(fieldKey) && parseRefType(value)) {
      // source_intent 字段在 task 类型下支持内联编辑
      const canEdit = fieldKey === 'source_intent' && objType === 'task' && objId && onRefresh;
      if (canEdit) {
        const handleSelect = async (intentId: string) => {
          if (!objId || !onRefresh) return;
          setSaving(true);
          try {
            await patchObjectField('task', objId, 'source_intent', intentId);
            setEditingSourceIntent(false);
            onRefresh();
          } catch {
            // keep selector open on error
          } finally {
            setSaving(false);
          }
        };
        return (
          <div className="relative">
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <ReferenceCard refs={[value]} />
              </div>
              <button
                onClick={() => setEditingSourceIntent(true)}
                disabled={saving}
                className="shrink-0 rounded-md border border-ldvh-border p-1.5 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary disabled:opacity-50"
                title={locale === 'en' ? 'Edit source intent' : '编辑来源意图'}
              >
                <Pencil size={13} />
              </button>
            </div>
            {editingSourceIntent && (
              <IntentSelector
                currentIntentId={value}
                onSelect={handleSelect}
                onClose={() => setEditingSourceIntent(false)}
              />
            )}
          </div>
        );
      }
      return <ReferenceCard refs={[value]} />;
    }

    // 长文本（含换行）使用 SummaryText
    if (value.includes('\n') || value.length > 200) {
      return <SummaryText value={value} />;
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
      // related_docs 字段使用 DocPreviewLink 组件
      if (fieldKey === 'related_docs') {
        return <DocPreviewLink docs={value as string[]} />;
      }
      // deliverables 字段使用 DocPreviewLink 组件
      if (fieldKey === 'deliverables') {
        return <DocPreviewLink docs={value as string[]} />;
      }
      // 引用字段使用 ReferenceCard 组件
      if (REFERENCE_FIELDS.includes(fieldKey)) {
        return <ReferenceCard refs={value as string[]} />;
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
            <FieldValue fieldKey={fieldKey} value={item} depth={depth + 1} locale={locale} objType={objType} objId={objId} onRefresh={onRefresh} />
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
                <FieldValue fieldKey={k} value={v} depth={depth + 1} locale={locale} objType={objType} objId={objId} onRefresh={onRefresh} />
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
