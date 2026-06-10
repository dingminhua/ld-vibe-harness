import { useEffect, useState, useCallback, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronRight, FileText, Code2, Info, Pencil } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import ChecklistCard from '@/components/ChecklistCard';
import ReferenceCard from '@/components/ReferenceCard';
import SummaryText from '@/components/SummaryText';
import DocPreviewLink from '@/components/DocPreviewLink';
import EvidenceBlock from '@/components/EvidenceBlock';
import IntentSelector from '@/components/IntentSelector';
import { fetchObjectDetail, patchObjectField, type ObjectDetail } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import { getTypeDescription, getStatusHint } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';

/** 字段分组定义 */
const META_KEYS = ['id', 'type', 'status', 'created', 'updated', 'closed_at', 'title', 'title_en', 'title_zh', 'aggregated_deliverables', 'aggregated_docs'];
const TASK_AUXILIARY_META_KEYS = ['category', 'priority', 'severity', 'tags', 'scope', 'impact', 'assignee'];
const AUXILIARY_META_KEYS_BY_TYPE: Record<string, string[]> = {
  task: TASK_AUXILIARY_META_KEYS,
  profile: ['project_name', 'project_kind', 'language', 'framework'],
  pitfall: ['severity', 'repeatability', 'tags'],
};
/** 长文本字段（用 SummaryText 组件渲染，支持展开/收起） */
const SUMMARY_TEXT_FIELDS = [
  'description', 'context', 'consequences', 'success_criteria', 'constraints',
  'rationale', 'observation', 'analysis', 'mitigation', 'resolution',
  'symptoms', 'trigger_conditions', 'root_cause', 'avoidance', 'applicability',
  'governance_scope', 'archive_reason', 'notes', 'transition_reasons',
];
/** 引用字段（用 ReferenceCard 组件渲染） */
const REFERENCE_FIELDS = [
  'blocked_by', 'source_intent', 'parent_task', 'related_intents', 'related_tasks',
  'related_adrs', 'related_memos', 'related_pitfalls', 'related_profiles',
  'source_tasks', 'source_memos', 'superseded_by',
];
const DOC_LINK_FIELDS = ['related_docs', 'deliverables', 'affected_docs', 'related_rules', 'superseded_by'];
const PATH_TEXT_FIELDS = ['project_path', 'ldvh_base_path', 'docs_path', 'rules_path', 'skills_path'];
/** 可折叠的关联内容字段（intent 类型默认展开，其他类型默认折叠） */
const COLLAPSIBLE_FIELDS = [
  'related_intents', 'related_tasks', 'related_docs', 'related_adrs', 'related_memos',
  'related_pitfalls', 'related_profiles', 'deliverables', 'affected_docs', 'related_rules',
  'source_tasks', 'source_memos', 'blocked_by',
];
/** Task 类型字段展示优先顺序 */
const TASK_FIELD_ORDER = ['acceptance', 'blocked_by', 'related_docs', 'deliverables'];
const FIELD_ORDER_BY_TYPE: Record<string, string[]> = {
  task: TASK_FIELD_ORDER,
  profile: [
    'description', 'project_path', 'ldvh_base_path', 'docs_path',
    'governance_scope', 'related_intents', 'related_tasks', 'related_adrs',
    'related_memos', 'related_pitfalls', 'related_docs', 'related_changes',
    'status_history', 'notes',
  ],
  pitfall: [
    'symptoms', 'trigger_conditions', 'root_cause', 'resolution', 'verification',
    'avoidance', 'applicability', 'source_tasks', 'source_memos', 'related_intents',
    'related_adrs', 'related_profiles', 'related_docs', 'related_rules',
    'related_changes', 'superseded_by', 'archive_reason', 'status_history', 'notes',
  ],
};

/** 对象类型中英映射 */
const TYPE_LOCALES: Record<string, { zh: string; en: string }> = {
  intent: { zh: '意图', en: 'Intent' },
  task: { zh: '任务', en: 'Task' },
  adr: { zh: 'ADR', en: 'ADR' },
  pitfall: { zh: '踩坑', en: 'Pitfall' },
  memo: { zh: '备忘', en: 'Memo' },
  profile: { zh: '画像', en: 'Profile' },
  change: { zh: '变更', en: 'Change' },
};

/** 字段名中英映射 */
const FIELD_LABEL_LOCALES: Record<string, { zh: string; en: string }> = {
  source: { zh: '来源', en: 'Source' },
  description: { zh: '描述', en: 'Description' },
  success_criteria: { zh: '成功标准', en: 'Success Criteria' },
  constraints: { zh: '约束', en: 'Constraints' },
  acceptance: { zh: '验收标准', en: 'Acceptance' },
  verification: { zh: '验证方式', en: 'Verification' },
  notes: { zh: '备注', en: 'Notes' },
  symptoms: { zh: '问题现象', en: 'Symptoms' },
  trigger_conditions: { zh: '触发条件', en: 'Trigger Conditions' },
  root_cause: { zh: '根因', en: 'Root Cause' },
  avoidance: { zh: '规避策略', en: 'Avoidance' },
  applicability: { zh: '适用范围', en: 'Applicability' },
  archive_reason: { zh: '归档原因', en: 'Archive Reason' },
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
  related_intents: { zh: '关联意图', en: 'Related Intents' },
  related_memos: { zh: '关联备忘', en: 'Related Memos' },
  related_pitfalls: { zh: '关联踩坑', en: 'Related Pitfalls' },
  related_profiles: { zh: '关联画像', en: 'Related Profiles' },
  source_tasks: { zh: '来源任务', en: 'Source Tasks' },
  source_memos: { zh: '来源备忘', en: 'Source Memos' },
  superseded_by: { zh: '替代来源', en: 'Superseded By' },
  related_changes: { zh: '关联变更', en: 'Related Changes' },
  scope: { zh: '范围', en: 'Scope' },
  impact: { zh: '影响范围', en: 'Impact' },
  severity: { zh: '严重程度', en: 'Severity' },
  category: { zh: '分类', en: 'Category' },
  priority: { zh: '优先级', en: 'Priority' },
  assignee: { zh: '执行者', en: 'Assignee' },
  tags: { zh: '标签', en: 'Tags' },
  path: { zh: '路径', en: 'Path' },
  project_name: { zh: '项目名称', en: 'Project Name' },
  project_kind: { zh: '项目类型', en: 'Project Kind' },
  project_path: { zh: '项目路径', en: 'Project Path' },
  ldvh_base_path: { zh: '事实实例路径', en: 'LDVH Base Path' },
  docs_path: { zh: '文档路径', en: 'Docs Path' },
  governance_scope: { zh: '管辖范围', en: 'Governance Scope' },
  language: { zh: '语言', en: 'Language' },
  framework: { zh: '框架', en: 'Framework' },
  repeatability: { zh: '复现概率', en: 'Repeatability' },
  related_rules: { zh: '承接规则', en: 'Related Rules' },
  status_history: { zh: '状态记录', en: 'Status History' },
  changes: { zh: '变更列表', en: 'Changes' },
  related_docs: { zh: '关联文档', en: 'Related Docs' },
  deliverables: { zh: '产出物', en: 'Deliverables' },
};

export default function ObjectDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const { t, getStatus, locale } = useI18n();



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
          <p className="ldvh-meta text-red-400">{error}</p>
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
  const auxiliaryMetaKeys = AUXILIARY_META_KEYS_BY_TYPE[objType] || [];
  const contentEntries = Object.entries(obj).filter(
    ([key]) => !META_KEYS.includes(key) && !auxiliaryMetaKeys.includes(key)
  );

  // 对有明确契约顺序的对象类型做语义排序
  const fieldOrder = FIELD_ORDER_BY_TYPE[objType] || [];
  if (fieldOrder.length > 0) {
    contentEntries.sort((a, b) => {
      const aIdx = fieldOrder.indexOf(a[0]);
      const bIdx = fieldOrder.indexOf(b[0]);
      if (aIdx !== -1 && bIdx !== -1) return aIdx - bIdx;
      if (aIdx !== -1) return -1;
      if (bIdx !== -1) return 1;
      return 0;
    });
  }

  const auxiliaryMetaEntries = getAuxiliaryMetaEntries(obj, objType);

  // 生成真正的 YAML 源码
  const yamlSource = objectToYaml(obj);
  const activeStatus = searchParams.get('status');
  const listSearch = searchParams.toString();
  const listPath = `/objects/${objType}${listSearch ? `?${listSearch}` : ''}`;
  const navigateToListWithStatus = (status: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    if (status) {
      nextParams.set('status', status);
    } else {
      nextParams.delete('status');
    }
    const nextSearch = nextParams.toString();
    navigate(`/objects/${objType}${nextSearch ? `?${nextSearch}` : ''}`);
  };

  return (
    <div className="flex h-full">
      {/* Main content area */}
      <div className="flex-1 overflow-y-auto rounded-none transition-[margin] duration-300">
        <div className="mx-auto max-w-4xl p-6">
          <ObjectStatusFilter
            type={objType}
            activeStatus={activeStatus}
            onChange={navigateToListWithStatus}
            className="mb-4"
          />

          {/* Header */}
          <div className="mb-6">
            <button
              onClick={() => navigate(listPath)}
              className="ldvh-body-muted mb-3 flex items-center gap-1.5 rounded-md px-2 py-1 transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
            >
              <ArrowLeft size={14} />
              {t('objectDetail.back')}
            </button>
            <div className="flex items-start gap-3">
              <span
                className="ldvh-chip mt-1 shrink-0 rounded px-2 py-0.5"
                style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
              >
                {TYPE_LOCALES[objType] ? (locale === 'en' ? TYPE_LOCALES[objType].en : TYPE_LOCALES[objType].zh) : objType}
              </span>
              <div className="min-w-0 flex-1">
                <h1 className="ldvh-page-title">{displayTitle}</h1>
                <p className="ldvh-meta mt-0.5">{objId}</p>
                {typeDesc && (
                  <p className="ldvh-caption mt-1">{typeDesc}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1.5">
                <StatusBadge status={objStatus} statusLabel={getStatus(objStatus)} size="md" />
                {statusHint && (
                  <span className="ldvh-caption">{statusHint}</span>
                )}
              </div>
            </div>
            {objStatus === 'review_needed' && (
              <div className="mt-3 flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                <Info size={14} className="shrink-0 text-amber-400" />
                <span className="ldvh-caption text-amber-300">{t('objectDetail.humanGateTip')}</span>
              </div>
            )}
          </div>

          {/* Metadata row */}
          <div className="mb-6 flex flex-wrap gap-2">
            <MetaChip label={t('objectDetail.created')} value={obj.created as string || '-'} />
            <MetaChip label={t('objectDetail.updated')} value={obj.updated as string || '-'} />
            {obj.closed_at && <MetaChip label={t('objectDetail.closedAt')} value={obj.closed_at as string} />}
            {auxiliaryMetaEntries.map(([key, value]) => (
              <MetaChip key={key} label={getFieldLabel(key, locale)} value={formatAuxiliaryMetaValue(value)} />
            ))}
          </div>

          {/* Content fields */}
          {objType === 'task' ? (
            <TaskReadingLayout obj={obj} locale={locale} objType={objType} objId={objId} onRefresh={refreshDetail} />
          ) : (
            <div className="mb-6 flex flex-col gap-5">
              {contentEntries.map(([key, value]) => (
                <ContentField key={key} fieldKey={key} value={value} locale={locale} objType={objType} objId={objId} onRefresh={refreshDetail} />
              ))}
            </div>
          )}

          {/* 聚合区域 - 仅 Intent 类型显示 */}
          {objType === 'intent' && (hasAggregatedDeliverables || hasAggregatedDocs) && (
            <div className="mb-6 flex flex-col gap-5">
              {hasAggregatedDeliverables && (
                <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <FileText size={13} className="text-ldvh-accent" />
                    <h4 className="ldvh-caption-strong tracking-wide">
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
                    <h4 className="ldvh-caption-strong tracking-wide">
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
              className="ldvh-body-muted flex w-full items-center gap-2 p-3 transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary"
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
    </div>
  );
}

/** 元信息小标签 */
function MetaChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5 rounded-md border border-ldvh-border bg-ldvh-panel px-2.5 py-1">
      <span className="ldvh-caption">{label}</span>
      <span className="ldvh-meta-primary">{value}</span>
    </div>
  );
}

function TaskReadingLayout({ obj, locale, objType, objId, onRefresh }: { obj: Record<string, unknown>; locale: string; objType: string; objId: string; onRefresh: () => void }) {
  const hidden = new Set(['source', 'description', 'source_intent', 'acceptance', 'verification', 'closure_evidence', 'deliverables', 'related_docs', 'affected_docs', 'blocked_by', ...TASK_AUXILIARY_META_KEYS, ...META_KEYS]);
  const otherEntries = Object.entries(obj).filter(([key, value]) => !hidden.has(key) && value !== null && value !== undefined && value !== '');

  return (
    <div className="mb-6 flex flex-col gap-5">
      <TaskSection title="任务目标" tone="primary">
        {obj.description ? <SummaryText value={String(obj.description)} /> : <EmptyHint text="未记录任务描述" />}
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {obj.source && <TaskInlineField label="来源" value={<SummaryText value={String(obj.source)} />} />}
          {obj.source_intent && (
            <TaskInlineField
              label="来源意图"
              value={<FieldValue fieldKey="source_intent" value={obj.source_intent} depth={0} locale={locale} objType={objType} objId={objId} onRefresh={onRefresh} />}
            />
          )}
        </div>
      </TaskSection>

      <TaskSection title="验收标准" tone="checklist">
        {obj.acceptance ? <ChecklistCard value={String(obj.acceptance)} /> : <EmptyHint text="未记录验收标准" />}
      </TaskSection>

      <div className="grid gap-5 lg:grid-cols-2">
        <TaskSection title="验证方式" tone="evidence">
          {obj.verification ? <EvidenceBlock value={String(obj.verification)} /> : <EmptyHint text="未记录验证方式" />}
        </TaskSection>
        <TaskSection title="关闭证据" tone="evidence">
          {obj.closure_evidence ? <EvidenceBlock value={String(obj.closure_evidence)} /> : <EmptyHint text="尚未记录关闭证据" />}
        </TaskSection>
      </div>

      <TaskSection title="产出与文档" tone="docs">
        <div className="grid gap-4 lg:grid-cols-3">
          <TaskDocGroup label="产出物" docs={obj.deliverables as string[] | undefined} />
          <TaskDocGroup label="关联文档" docs={obj.related_docs as string[] | undefined} />
          <TaskDocGroup label="影响文档" docs={obj.affected_docs as string[] | undefined} />
        </div>
      </TaskSection>

      {obj.blocked_by && Array.isArray(obj.blocked_by) && obj.blocked_by.length > 0 && (
        <TaskSection title="前置依赖" tone="default">
          <ReferenceCard refs={obj.blocked_by as string[]} />
        </TaskSection>
      )}

      {otherEntries.length > 0 && (
        <TaskSection title="其他字段" tone="default">
          <div className="flex flex-col gap-3">
            {otherEntries.map(([key, value]) => (
              <ContentField key={key} fieldKey={key} value={value} locale={locale} objType={objType} objId={objId} onRefresh={onRefresh} />
            ))}
          </div>
        </TaskSection>
      )}
    </div>
  );
}

function getAuxiliaryMetaEntries(obj: Record<string, unknown>, objType: string) {
  const keys = AUXILIARY_META_KEYS_BY_TYPE[objType] || [];
  return keys
    .map((key) => [key, obj[key]] as [string, unknown])
    .filter(([, value]) => value !== null && value !== undefined && value !== '' && (!Array.isArray(value) || value.length > 0));
}

function getFieldLabel(fieldKey: string, locale: string) {
  const labelEntry = FIELD_LABEL_LOCALES[fieldKey];
  return labelEntry ? (locale === 'en' ? labelEntry.en : labelEntry.zh) : fieldKey.replace(/_/g, ' ');
}

function formatAuxiliaryMetaValue(value: unknown) {
  return Array.isArray(value) ? value.join(' · ') : String(value);
}

function TaskSection({ title, tone, children }: { title: string; tone: 'primary' | 'checklist' | 'evidence' | 'docs' | 'default'; children: ReactNode }) {
  const toneClass = {
    primary: 'border-ldvh-accent/30 bg-ldvh-panel',
    checklist: 'border-emerald-500/25 bg-ldvh-panel',
    evidence: 'border-sky-500/25 bg-ldvh-panel',
    docs: 'border-violet-500/25 bg-ldvh-panel',
    default: 'border-ldvh-border bg-ldvh-panel',
  }[tone];

  return (
    <section className={`rounded-xl border p-4 ${toneClass}`}>
      <h2 className="ldvh-section-title mb-3 flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-ldvh-accent" />
        {title}
      </h2>
      {children}
    </section>
  );
}

function TaskInlineField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-bg/40 p-3">
      <div className="ldvh-caption-strong mb-1 tracking-wide">{label}</div>
      {value}
    </div>
  );
}

function TaskDocGroup({ label, docs }: { label: string; docs?: string[] }) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-bg/40 p-3">
      <div className="ldvh-caption-strong mb-2 tracking-wide">{label}</div>
      {docs && docs.length > 0 ? <DocPreviewLink docs={docs} /> : <EmptyHint text="空" />}
    </div>
  );
}

function isPreviewableDocPath(value: string) {
  return value.startsWith('http://') || value.startsWith('https://') || /^(docs\/|specs\/|web\/docs\/)/.test(value);
}

function PathText({ value }: { value: string }) {
  return (
    <span className="ldvh-meta-primary break-all rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1">
      {value}
    </span>
  );
}

function StringList({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span key={i} className="ldvh-chip rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-0.5 text-ldvh-text-primary">
          {item}
        </span>
      ))}
    </div>
  );
}

function DocumentOrTextList({ items }: { items: string[] }) {
  const docs = items.filter(isPreviewableDocPath);
  const rest = items.filter((item) => !isPreviewableDocPath(item));
  return (
    <div className="flex flex-col gap-2">
      {docs.length > 0 && <DocPreviewLink docs={docs} />}
      {rest.length > 0 && <StringList items={rest} />}
    </div>
  );
}

function EmptyHint({ text }: { text: string }) {
  return <span className="ldvh-body-muted">{text}</span>;
}

/** 内容字段：根据字段类型选择渲染方式和样式 */
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
        <h4 className="ldvh-caption-strong tracking-wide">{label}</h4>
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

function FieldValue({ fieldKey, value, depth, locale, objType, objId, onRefresh }: { fieldKey: string; value: unknown; depth: number; locale: string; objType?: string; objId?: string; onRefresh?: () => void }) {
  const { t } = useI18n();
  const [editingSourceIntent, setEditingSourceIntent] = useState(false);
  const [saving, setSaving] = useState(false);
  if (value === null || value === undefined) {
    return <span className="ldvh-caption italic">{t('common.null')}</span>;
  }

  // 字符串
  if (typeof value === 'string') {
    // 空字符串不显示
    if (value === '') return null;

    // acceptance 字段使用 ChecklistCard 组件
    if (fieldKey === 'acceptance') {
      return <ChecklistCard value={value} />;
    }

    // closure_evidence 字段使用 EvidenceBlock 组件（嵌入模式）
    if (fieldKey === 'closure_evidence') {
      return <EvidenceBlock value={value} embedded />;
    }

    // verification 字段使用 EvidenceBlock 组件（嵌入模式）
    if (fieldKey === 'verification') {
      return <EvidenceBlock value={value} embedded />;
    }

    if (DOC_LINK_FIELDS.includes(fieldKey) && isPreviewableDocPath(value)) {
      return <DocPreviewLink docs={[value]} />;
    }

    if (PATH_TEXT_FIELDS.includes(fieldKey)) {
      return <PathText value={value} />;
    }

    // success_criteria 含 checklist 时使用 ChecklistCard（12-工作模型字段内容格式规范 §5）
    if (fieldKey === 'success_criteria' && /^\s*- \[[ xX]\]/m.test(value)) {
      return <ChecklistCard value={value} />;
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
    return <span className="ldvh-body">{value}</span>;
  }

  // 布尔值
  if (typeof value === 'boolean') {
    return (
      <span className={`ldvh-chip rounded px-1.5 py-0.5 ${value ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
        {value ? t('common.true') : t('common.false')}
      </span>
    );
  }

  // 数字
  if (typeof value === 'number') {
    return <span className="ldvh-meta-primary text-ldvh-accent">{value}</span>;
  }

  // 数组
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="ldvh-caption italic">{t('common.empty')}</span>;
    }

    // 字符串数组
    if (typeof value[0] === 'string') {
      // related_docs 字段使用 DocPreviewLink 组件
      if (DOC_LINK_FIELDS.includes(fieldKey)) {
        return <DocumentOrTextList items={value as string[]} />;
      }
      // 引用字段使用 ReferenceCard 组件
      if (REFERENCE_FIELDS.includes(fieldKey)) {
        return <ReferenceCard refs={value as string[]} />;
      }
      return <StringList items={value as string[]} />;
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
              <span className="ldvh-caption shrink-0 rounded border border-ldvh-border bg-ldvh-bg px-1.5 py-0.5">
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

  return <span className="ldvh-body">{String(value)}</span>;
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
