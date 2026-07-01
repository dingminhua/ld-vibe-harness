import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowLeft, BookOpenText, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Code2, ExternalLink, FileText } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import StatusBadge from '@/components/StatusBadge';
import ChecklistCard from '@/components/ChecklistCard';
import ReferenceCard from '@/components/ReferenceCard';
import SummaryText from '@/components/SummaryText';
import DocPreviewLink from '@/components/DocPreviewLink';
import EvidenceBlock from '@/components/EvidenceBlock';
import CopyPathButton from '@/components/CopyPathButton';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { ExecutionFlowBar, ExecutionFlowMarker } from '@/components/ExecutionFlowStatus';
import { fetchObjectDetail, fetchObjects, type ObjectDetail, type ObjectItem, type RelatedObjectSummary } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { formatDateTime } from '@/utils/dateFormat';
import { getStatusColor } from '@/utils/statusColors';
import { executionFlowRowClass, getExecutionFlowLabel, getExecutionFlowTone, sortWorkCaseExecutionItems } from '@/utils/executionFlowStatus';
import { getSignalClassName, getSignalText, isSignalField } from '@/utils/objectSignals';
import { usePanel } from '@/utils/panelContext';
import { isWorkCaseResultReviewStatus } from '@/utils/workcaseStatus';
import {
  CHECKLIST_COMPAT_FIELDS,
  COLLAPSIBLE_FIELDS,
  DOC_LINK_FIELDS,
  EVIDENCE_FIELDS,
  PATH_TEXT_FIELDS,
  REFERENCE_FIELDS,
  SUMMARY_TEXT_FIELDS,
  getPreviewableDocPath,
  hasChecklist,
  isObjectRef,
  isPreviewablePathForField,
} from '@/utils/fieldFormats';

/** 字段分组定义 */
const META_KEYS = [
  'id',
  'type',
  'status',
  'created',
  'updated',
  'closed_at',
  'title',
  'title_en',
  'title_zh',
  'path',
  'aggregated_related_docs',
  'aggregated_related_adrs',
  'aggregated_related_sparks',
  'aggregated_related_pitfalls',
  'aggregated_execution_refs',
];
const COMMON_AUXILIARY_META_KEYS = ['priority', 'importance', 'tags', 'scope', 'impact', 'assignee'];
const AUXILIARY_META_KEYS_BY_TYPE: Record<string, string[]> = {
  spark: ['priority', 'tags', 'source'],
  study: ['tags'],
  pitfall: ['tags'],
};
const FIELD_ORDER_BY_TYPE: Record<string, string[]> = {
  workcase: [
    'priority', 'description', 'success_criteria', 'source',
    'orchestration', 'verification_evidence', 'closure_evidence', 'related_workcases',
    'related_docs', 'related_adrs', 'related_sparks', 'related_pitfalls',
  ],
  adr: [
    'context', 'decision', 'consequences',
    'related_rules', 'archive_reason', 'deprecated_reason',
    'related_workcases', 'related_adrs', 'related_sparks',
  ],
  pitfall: [
    'symptoms', 'trigger_conditions', 'root_cause', 'resolution', 'verification',
    'avoidance', 'applicability', 'source_sparks',
    'related_adrs', 'related_docs', 'related_rules',
    'archive_reason', 'discard_reason', 'notes',
  ],
  spark: [
    'description', 'evolution', 'resolved_to', 'resolved_at', 'discard_reason',
    'source', 'source_detail', 'related_workcases',
    'related_adrs', 'related_studies', 'related_docs',
  ],
  study: [
    'user_intent', 'summary', 'conclusion', 'report_body', 'urls',
    'related_sparks',
    'related_adrs', 'related_pitfalls', 'related_docs', 'archive_reason',
  ],
};

const STUDY_READING_NODE_FIELDS = new Set(['user_intent', 'summary', 'conclusion', 'report_body']);
type ReadingNodeState = 'collapsed' | 'expanded';
const RELATED_OBJECT_FIELD_ORDER: Record<string, number> = {
  related_workcases: 21,
  related_adrs: 22,
  related_pitfalls: 23,
  related_sparks: 20,
  related_studies: 24,
};
export type RelatedContentEntry = [string, unknown[]];
type RelatedAssociationValue = {
  ref: string;
  title?: string;
  summary?: string;
};

function normalizeRelatedFieldKey(fieldKey: string) {
  return fieldKey.startsWith('aggregated_') ? fieldKey.slice('aggregated_'.length) : fieldKey;
}

function isRelatedContentField(fieldKey: string) {
  const normalized = normalizeRelatedFieldKey(fieldKey);
  return normalized === 'urls' || normalized.startsWith('related_');
}

export function sortRelatedContentEntries(entries: RelatedContentEntry[]) {
  return [...entries].sort((a, b) => {
    const aKey = normalizeRelatedFieldKey(a[0]);
    const bKey = normalizeRelatedFieldKey(b[0]);
    const aOrder = RELATED_OBJECT_FIELD_ORDER[aKey];
    const bOrder = RELATED_OBJECT_FIELD_ORDER[bKey];
    const aIsObject = aOrder !== undefined;
    const bIsObject = bOrder !== undefined;

    if (aIsObject && bIsObject) return aOrder - bOrder;
    if (aIsObject) return -1;
    if (bIsObject) return 1;
    return aKey.localeCompare(bKey, 'en');
  });
}

export function splitRelatedContentEntries(entries: Array<[string, unknown]>) {
  const primaryEntries: Array<[string, unknown]> = [];
  const relatedEntries: RelatedContentEntry[] = [];

  entries.forEach((entry) => {
    if (isRelatedContentField(entry[0])) {
      if (Array.isArray(entry[1]) && hasDetailContent(entry[1])) {
        relatedEntries.push([entry[0], entry[1]]);
      }
    }
    else primaryEntries.push(entry);
  });

  return {
    primaryEntries,
    relatedEntries: sortRelatedContentEntries(relatedEntries),
  };
}

export function getObjectDetailContentEntries(obj: Record<string, unknown>, objType: string) {
  const auxiliaryMetaKeys = Array.from(new Set([...(AUXILIARY_META_KEYS_BY_TYPE[objType] || []), ...COMMON_AUXILIARY_META_KEYS]));
  const contentEntries = Object.entries(obj).filter(
    ([key]) => !META_KEYS.includes(key) && !auxiliaryMetaKeys.includes(key)
  );

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

  return contentEntries;
}

/** 对象类型中英映射 */
const TYPE_LOCALES: Record<string, { zh: string; en: string }> = {
  workcase: { zh: '工作', en: 'WorkCase' },
  adr: { zh: '决策', en: 'ADR' },
  pitfall: { zh: '经验', en: 'Pitfall' },
  spark: { zh: '火花', en: 'Spark' },
  study: { zh: '研究', en: 'Study' },
  change: { zh: '提交', en: 'Commit' },
};

/** 字段名中英映射 */
export const FIELD_LABEL_LOCALES: Record<string, { zh: string; en: string }> = {
  id: { zh: 'ID', en: 'ID' },
  type: { zh: '类型', en: 'Type' },
  title: { zh: '标题', en: 'Title' },
  title_en: { zh: '英文标题', en: 'English Title' },
  title_zh: { zh: '中文标题', en: 'Chinese Title' },
  status: { zh: '状态', en: 'Status' },
  created: { zh: '创建时间', en: 'Created' },
  updated: { zh: '更新时间', en: 'Updated' },
  closed_at: { zh: '关闭时间', en: 'Closed At' },
  date: { zh: '日期', en: 'Date' },
  source: { zh: '来源', en: 'Source' },
  source_detail: { zh: '来源说明', en: 'Source Detail' },
  user_intent: { zh: '用户意图', en: 'User Intent' },
  description: { zh: '描述', en: 'Description' },
  evolution: { zh: '演变记录', en: 'Evolution' },
  report_body: { zh: '报告正文', en: 'Report Body' },
  summary: { zh: '摘要', en: 'Summary' },
  conclusion: { zh: '结论', en: 'Conclusion' },
  details: { zh: '详情', en: 'Details' },
  background: { zh: '背景', en: 'Background' },
  motivation: { zh: '动机', en: 'Motivation' },
  outcome: { zh: '结果', en: 'Outcome' },
  next_steps: { zh: '后续步骤', en: 'Next Steps' },
  lessons: { zh: '经验教训', en: 'Lessons' },
  success_criteria: { zh: '成功标准', en: 'Success Criteria' },
  constraints: { zh: '约束', en: 'Constraints' },
  acceptance: { zh: '验收标准', en: 'Acceptance' },
  verification: { zh: '验证', en: 'Verification' },
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
  workcase: { zh: '工作', en: 'WorkCase' },
  orchestration: { zh: '编排', en: 'Orchestration' },
  execution_items: { zh: '执行项', en: 'Execution Items' },
  mode: { zh: '模式', en: 'Mode' },
  role: { zh: '角色', en: 'Role' },
  input_refs: { zh: '输入引用', en: 'Input Refs' },
  expected_output: { zh: '期望输出', en: 'Expected Output' },
  result_summary: { zh: '结果摘要', en: 'Result Summary' },
  evidence_refs: { zh: '证据引用', en: 'Evidence Refs' },
  blocking_reason: { zh: '阻塞原因', en: 'Blocking Reason' },
  closure_evidence: { zh: '关闭证据', en: 'Closure Evidence' },
  verification_evidence: { zh: '验证证据', en: 'Verification Evidence' },
  review_requested_at: { zh: '请求关闭确认时间', en: 'Review Requested At' },
  plan_confirmed_at: { zh: '方案确认时间', en: 'Plan Confirmed At' },
  closure_requested_at: { zh: '关闭确认请求时间', en: 'Closure Requested At' },
  closure_outcome: { zh: '关闭结果', en: 'Closure Outcome' },
  residual_risks: { zh: '残留风险', en: 'Residual Risks' },
  followup_refs: { zh: '后续承接', en: 'Follow-up Refs' },
  revision_history: { zh: '修订记录', en: 'Revision History' },
  transition_reasons: { zh: '流转记录', en: 'Transition Reasons' },
  options: { zh: '选项', en: 'Options' },
  decision: { zh: '决策', en: 'Decision' },
  related_workcases: { zh: '关联工作', en: 'Related Work Cases' },
  related_adrs: { zh: '关联决策', en: 'Related ADRs' },
  related_sparks: { zh: '关联火花', en: 'Related Sparks' },
  related_studies: { zh: '关联研究', en: 'Related Studies' },
  related_pitfalls: { zh: '关联经验', en: 'Related Pitfalls' },
  source_objects: { zh: '来源对象', en: 'Source Objects' },
  related_objects: { zh: '关联对象', en: 'Related Objects' },
  source_sparks: { zh: '来源火花', en: 'Source Sparks' },
  resolved_to: { zh: '分流目标', en: 'Routed To' },
  resolved_at: { zh: '分流时间', en: 'Routed At' },
  discard_reason: { zh: '废弃原因', en: 'Discard Reason' },
  deprecated_reason: { zh: '废弃原因', en: 'Deprecated Reason' },
  aggregated_execution_refs: { zh: '执行引用', en: 'Execution Refs' },
  scope: { zh: '范围', en: 'Scope' },
  impact: { zh: '影响范围', en: 'Impact' },
  category: { zh: '分类', en: 'Category' },
  priority: { zh: '优先级', en: 'Priority' },
  importance: { zh: '重要程度', en: 'Importance' },
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
  related_rules: { zh: '规范', en: 'Specs' },
  urls: { zh: '网址', en: 'URLs' },
  related_docs: { zh: '关联文档', en: 'Related Docs' },
  aggregated_related_docs: { zh: '聚合关联文档', en: 'Aggregated Related Docs' },
  aggregated_related_adrs: { zh: '聚合关联决策', en: 'Aggregated Related ADRs' },
  aggregated_related_sparks: { zh: '聚合关联火花', en: 'Aggregated Related Sparks' },
  aggregated_related_pitfalls: { zh: '聚合关联经验', en: 'Aggregated Related Pitfalls' },
  at: { zh: '时间', en: 'At' },
  from: { zh: '前状态', en: 'From' },
  to: { zh: '后状态', en: 'To' },
  actor: { zh: '执行者', en: 'Actor' },
  reason: { zh: '原因', en: 'Reason' },
};

const FIELD_VALUE_LOCALES: Record<string, Record<string, { zh: string; en: string }>> = {
  category: {
    question: { zh: '问题', en: 'Question' },
    discovery: { zh: '发现', en: 'Discovery' },
    gap: { zh: '缺口', en: 'Gap' },
  },
  priority: {
    P0: { zh: 'P0', en: 'P0' },
    P1: { zh: 'P1', en: 'P1' },
    P2: { zh: 'P2', en: 'P2' },
    P3: { zh: 'P3', en: 'P3' },
  },
  importance: {
    high: { zh: '高', en: 'High' },
    medium: { zh: '中', en: 'Medium' },
    low: { zh: '低', en: 'Low' },
  },
};

export default function ObjectDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [relatedWorkCaseSummary, setRelatedWorkCaseSummary] = useState<ObjectItem | null>(null);
  const [relatedSummaryLoading, setRelatedSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const { t, getStatus, locale } = useI18n();



  useEffect(() => {
    if (!type || !id) return;
    let cancelled = false;
    setDetail(null);
    setRelatedWorkCaseSummary(null);
    setRelatedSummaryLoading(type === 'workcase');
    setError(null);

    fetchObjectDetail(type, id)
      .then((result) => {
        if (!cancelled) setDetail(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });


    if (type === 'workcase') {
      fetchObjects('workcase')
        .then((result) => {
          if (cancelled) return;
          setRelatedWorkCaseSummary(result.data?.items?.find((workcase) => workcase.id === id) ?? null);
        })
        .catch(() => {
          if (!cancelled) setRelatedWorkCaseSummary(null);
        })
        .finally(() => {
          if (!cancelled) setRelatedSummaryLoading(false);
        });
    }

    return () => {
      cancelled = true;
    };
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

  const displayTitle = (locale === 'en'
    ? ((obj.title_en as string) || obj.title as string)
    : ((obj.title_zh as string) || obj.title as string)) || objId;

  const contentEntries = getObjectDetailContentEntries(obj, objType);
  const { primaryEntries, relatedEntries } = splitRelatedContentEntries(contentEntries);

  const auxiliaryMetaEntries = getAuxiliaryMetaEntries(obj, objType);

  // 生成真正的 YAML 源码
  const yamlSource = objectToYaml(obj);
  const listSearch = searchParams.toString();
  const listPath = `/objects/${objType}${listSearch ? `?${listSearch}` : ''}`;
  const currentPath = `${location.pathname}${location.search}`;
  const returnPath = getReturnPath(location.state, currentPath) ?? listPath;
  const copyTarget = String(obj.path || detail.target || objId);

  return (
    <div className="flex h-full">
      {/* Main content area */}
      <div className="flex-1 overflow-y-auto rounded-none transition-[margin] duration-300">
        <div className="mx-auto max-w-4xl p-4 sm:p-6">
          <div className="sticky top-0 z-20 -mx-4 -mt-4 mb-6 border-b border-ldvh-border bg-ldvh-bg/95 px-4 pb-4 pt-4 backdrop-blur sm:-mx-6 sm:-mt-6 sm:px-6">
          {/* Header */}
          <div>
            <button
              onClick={() => navigate(returnPath)}
              className="ldvh-body-muted mb-3 flex items-center gap-1.5 rounded-md px-2 py-1 transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
            >
              <ArrowLeft size={14} />
              {t('objectDetail.back')}
            </button>
              <ObjectIdentityHeader
                title={displayTitle}
                id={objId}
                target={copyTarget}
                objectType={objType}
                typeColor={typeColor}
                typeLabel={TYPE_LOCALES[objType] ? (locale === 'en' ? TYPE_LOCALES[objType].en : TYPE_LOCALES[objType].zh) : objType}
                status={objStatus}
                statusLabel={getObjectStatusLocale(objType, objStatus, locale)}
                source={obj}
                locale={locale}
                created={formatDateTime(obj.created as string | undefined)}
                updated={formatDateTime(obj.updated as string | undefined)}
                closedAt={obj.closed_at ? formatDateTime(obj.closed_at as string) : undefined}
                auxiliaryMetaEntries={auxiliaryMetaEntries}
                copyLabel={t('common.copyObjectPath')}
                copiedLabel={t('common.copiedObjectPath')}
              />
          </div>
          </div>

          {/* Content fields */}
          {objType === 'workcase' ? (
            <WorkCaseReadingLayout
              obj={obj}
              summary={relatedWorkCaseSummary}
              loading={relatedSummaryLoading}
              locale={locale}
              getStatus={getStatus}
            />
          ) : objType === 'study' ? (
            <StudyReadingLayout
              obj={obj}
              extraEntries={primaryEntries}
              relatedEntries={relatedEntries}
              locale={locale}
              objectPath={typeof obj.path === 'string' ? obj.path : detail.target}
            />
          ) : objType === 'adr' ? (
            <AdrReadingLayout
              obj={obj}
              relatedEntries={relatedEntries}
              locale={locale}
            />
          ) : objType === 'pitfall' ? (
            <PitfallReadingLayout
              obj={obj}
              relatedEntries={relatedEntries}
              locale={locale}
            />
          ) : objType === 'spark' ? (
            <SparkReadingLayout
              obj={obj}
              relatedEntries={relatedEntries}
              locale={locale}
            />
          ) : (
            <div className="mb-6 flex flex-col gap-5">
              {primaryEntries.map(([key, value]) => (
                <ContentField
                  key={key}
                  fieldKey={key}
                  value={value}
                  locale={locale}
                  objType={objType}
                  objectPath={typeof obj.path === 'string' ? obj.path : detail.target}
                />
              ))}
              <RelatedContentSection entries={relatedEntries} locale={locale} />
            </div>
          )}

          {/* YAML source */}
          <div className="overflow-hidden rounded-xl border border-ldvh-border bg-ldvh-panel">
            <button
              onClick={() => setShowYaml(!showYaml)}
              className="ldvh-body-muted flex w-full items-center gap-2 p-3 transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary"
            >
              <Code2 size={14} />
              <span>{t('objectDetail.yamlSource')}</span>
              <span className="ml-auto">{showYaml ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</span>
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

function getReturnPath(state: unknown, currentPath: string): string | null {
  if (!state || typeof state !== 'object') return null;
  const from = (state as { from?: unknown }).from;
  if (typeof from !== 'string' || from.length === 0) return null;
  if (from === currentPath) return null;
  if (!from.startsWith('/')) return null;
  return from;
}

type LocalizedTitleItem = {
  id: string;
  title?: string;
  title_en?: string;
  title_zh?: string;
};

export function getLocalizedTitle(item: LocalizedTitleItem, locale: string): string {
  if (locale === 'en') return item.title_en || item.title || item.id;
  return item.title_zh || item.title || item.id;
}

export function ObjectIdentityHeader({
  title,
  id,
  target,
  objectType,
  typeColor,
  typeLabel,
  status,
  statusLabel,
  source,
  locale,
  created,
  updated,
  closedAt,
  auxiliaryMetaEntries = [],
  extraBadges,
  titleMetaEntries = [],
  customMetaEntries = [],
  copyLabel,
  copiedLabel,
  titleMetaAlign = 'content',
  showDefaultDates = true,
  showCopyAction = true,
  compact = false,
}: {
  title: string;
  id: string;
  target?: string;
  objectType: string;
  typeColor: string;
  typeLabel: string;
  status?: string;
  statusLabel?: string;
  source: Record<string, unknown>;
  locale: string;
  created: string;
  updated: string;
  closedAt?: string;
  auxiliaryMetaEntries?: Array<[string, unknown]>;
  extraBadges?: ReactNode;
  titleMetaEntries?: Array<{ label: string; value: ReactNode }>;
  customMetaEntries?: Array<{ label: string; value: ReactNode }>;
  copyLabel?: string;
  copiedLabel?: string;
  titleMetaAlign?: 'content' | 'actions' | 'footerEnd';
  showDefaultDates?: boolean;
  showCopyAction?: boolean;
  compact?: boolean;
}) {
  const { t } = useI18n();
  const TitleTag = compact ? 'h3' : 'h1';
  const titleClassName = compact ? 'ldvh-reading-title' : 'ldvh-page-title';
  const iconSize = compact ? 16 : 18;
  const statusColor = status ? getStatusColor(status) : null;
  const tagMetaEntry = auxiliaryMetaEntries.find(([key]) => key === 'tags');
  const remainingAuxiliaryMetaEntries = auxiliaryMetaEntries.filter(([key]) => key !== 'priority' && key !== 'tags');
  const hasFooterMeta = showDefaultDates
    || remainingAuxiliaryMetaEntries.length > 0
    || customMetaEntries.length > 0
    || Boolean(closedAt);
  const inlineTitleMeta = titleMetaAlign === 'content' ? titleMetaEntries : [];
  const actionAlignedTitleMeta = titleMetaAlign === 'actions' ? titleMetaEntries : [];
  const footerEndTitleMeta = titleMetaAlign === 'footerEnd' ? titleMetaEntries : [];
  return (
    <div className={compact ? 'min-w-0' : 'rounded-lg border border-ldvh-border bg-ldvh-panel px-4 py-3'}>
      <div className="flex min-w-0 items-center justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
            <span
              className="ldvh-chip shrink-0 rounded px-2 py-0.5"
              style={{ backgroundColor: `${typeColor}18`, color: typeColor }}
            >
              {typeLabel}
            </span>
            {status && statusColor && (
              <span
                className="ldvh-chip shrink-0 rounded px-2 py-0.5 font-mono"
                style={{
                  color: statusColor,
                  backgroundColor: `${statusColor}18`,
                }}
              >
                {statusLabel || status}
              </span>
            )}
            {extraBadges}
            <span className="ldvh-meta-muted min-w-0 truncate">{id}</span>
          </div>
          <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1">
            <TitleTag className={`${titleClassName} flex min-w-0 flex-1 basis-full items-center gap-2 break-words`}>
              <PriorityIcon source={source} type={objectType} locale={locale} size={compact ? 'sm' : 'lg'} />
              <ObjectTypeIcon type={objectType} size={iconSize} className="shrink-0" style={{ color: typeColor }} />
              <span className="min-w-0">{title}</span>
            </TitleTag>
            {inlineTitleMeta.length > 0 && (
              <div className="ml-auto flex min-w-0 basis-full flex-wrap items-center justify-end gap-x-4 gap-y-1 text-right">
                {inlineTitleMeta.map((entry) => (
                  <HeaderDateMeta key={entry.label} label={entry.label} value={entry.value} />
                ))}
              </div>
            )}
          </div>
        </div>
        {showCopyAction && (
          <div className="flex shrink-0 flex-col items-end justify-center gap-2">
            <CopyPathButton path={target} label={copyLabel} copiedLabel={copiedLabel} />
            {actionAlignedTitleMeta.length > 0 && (
              <div className="flex flex-wrap items-center justify-end gap-x-4 gap-y-1 text-right">
                {actionAlignedTitleMeta.map((entry) => (
                  <HeaderDateMeta key={entry.label} label={entry.label} value={entry.value} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {tagMetaEntry && (
        <div className="mt-2 flex min-w-0 flex-wrap items-center justify-start gap-x-4 gap-y-1 text-left">
          <HeaderDateMeta
            label={getFieldLabel(tagMetaEntry[0], locale)}
            value={formatAuxiliaryMetaValue(tagMetaEntry[0], tagMetaEntry[1], locale)}
            align="start"
          />
        </div>
      )}
      {hasFooterMeta && (
        <div className="mt-2 flex min-w-0 flex-wrap items-center justify-end gap-x-4 gap-y-1 text-right">
          {showDefaultDates && <HeaderDateMeta label={t('objectDetail.createdShort')} value={created} />}
          {showDefaultDates && <HeaderDateMeta label={t('objectDetail.updatedShort')} value={updated} />}
          {remainingAuxiliaryMetaEntries.map(([key, value]) => (
            <HeaderDateMeta
              key={key}
              label={getFieldLabel(key, locale)}
              value={formatAuxiliaryMetaValue(key, value, locale)}
            />
          ))}
          {customMetaEntries.map((entry) => (
            <HeaderDateMeta key={entry.label} label={entry.label} value={entry.value} />
          ))}
          {closedAt && <HeaderDateMeta label={t('objectDetail.closedAt')} value={closedAt} />}
        </div>
      )}
      {footerEndTitleMeta.length > 0 && (
        <div className="mt-2 flex min-w-0 flex-wrap items-center justify-end gap-x-4 gap-y-1 text-right">
          {footerEndTitleMeta.map((entry) => (
            <HeaderDateMeta key={entry.label} label={entry.label} value={entry.value} />
          ))}
        </div>
      )}
    </div>
  );
}

function HeaderDateMeta({ label, value, align = 'end' }: { label: string; value: ReactNode; align?: 'start' | 'end' }) {
  const valueClassName = typeof value === 'string'
    ? 'ldvh-meta-muted min-w-0 truncate text-ldvh-text-secondary'
    : 'min-w-0';
  const alignClassName = align === 'start' ? 'justify-start text-left' : 'justify-end text-right';
  return (
    <span className={`inline-flex min-w-0 items-center gap-1.5 ${alignClassName}`}>
      <span className="ldvh-caption shrink-0">{label}</span>
      <span className={valueClassName}>{value}</span>
    </span>
  );
}

export function DefinitionRow({
  label,
  value,
  muted = false,
  emphasis = false,
}: {
  label: string;
  value: unknown;
  muted?: boolean;
  emphasis?: boolean;
}) {
  if (!value || (typeof value === 'string' && value.trim().length === 0)) return null;
  return (
    <div className="grid gap-2 py-3 first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr]">
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{label}</div>
      <div className={`ldvh-definition-text min-w-0 ${muted ? 'opacity-85' : ''} ${emphasis ? 'rounded-md border border-amber-500/20 bg-amber-500/5 px-3 py-2' : ''}`}>
        <DefinitionValue value={String(value)} muted={muted} />
      </div>
    </div>
  );
}

function DefinitionValue({ value, muted = false }: { value: string; muted?: boolean }) {
  const lines = value
    .split('\n')
    .map((line) => normalizeDefinitionLine(line))
    .filter(Boolean);

  if (lines.length <= 1) {
    return <p className={muted ? 'ldvh-body-muted' : 'ldvh-body'}>{value}</p>;
  }

  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      {lines.map((line, index) => (
        <DefinitionStatement key={`${index}-${line}`} line={line} muted={muted} />
      ))}
    </div>
  );
}

function DefinitionStatement({ line, muted = false }: { line: string; muted?: boolean }) {
  const statement = splitDefinitionStatement(line);
  const textClassName = muted ? 'ldvh-body-muted' : 'ldvh-body';

  if (statement) {
    const tone = statement.term === '不包含'
      ? 'border-rose-500/20 bg-rose-500/5 text-rose-400'
      : 'border-ldvh-accent/20 bg-ldvh-accent/5 text-ldvh-accent';
    return (
      <div className="grid min-w-0 gap-2 py-0.5 sm:grid-cols-[4rem_1fr]">
        <span className={`ldvh-caption-strong inline-flex h-6 w-fit items-center rounded-md border px-1.5 ${tone}`}>
          {statement.term}
        </span>
        <p className={textClassName}>{statement.content}</p>
      </div>
    );
  }

  return (
    <div className="grid min-w-0 gap-2 py-0.5 sm:grid-cols-[0.625rem_1fr]">
      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-ldvh-text-secondary/45" aria-hidden="true" />
      <p className={textClassName}>{line}</p>
    </div>
  );
}

function splitDefinitionStatement(line: string): { term: string; content: string } | null {
  const match = line.match(/^([^：:]{1,6})[：:]\s*(.+)$/);
  if (!match) return null;
  const [, term, content] = match;
  return { term: term.trim(), content: content.trim() };
}

function normalizeDefinitionLine(line: string): string {
  return line
    .trim()
    .replace(/^[-*]\s+/, '')
    .replace(/^\d+[.)]\s+/, '')
    .replace(/^\[[ xX]\]\s+/, '')
    .trim();
}

export function MaterialRow({
  fieldKey,
  value,
  locale,
  referenceVariant = 'card',
}: {
  fieldKey: string;
  value: unknown;
  locale: string;
  referenceVariant?: 'card' | 'plain';
}) {
  if (!Array.isArray(value) || value.length === 0) return null;
  return (
    <div className="grid gap-2 py-3 first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr]">
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{getMaterialLabel(fieldKey, locale)}</div>
      <MaterialValue fieldKey={fieldKey} value={value} locale={locale} referenceVariant={referenceVariant} />
    </div>
  );
}

function MaterialValue({
  fieldKey,
  value,
  locale,
  referenceVariant = 'card',
}: {
  fieldKey: string;
  value: unknown[];
  locale: string;
  referenceVariant?: 'card' | 'plain';
}) {
  return (
    <div className="min-w-0">
      {DOC_LINK_FIELDS.includes(fieldKey) && typeof value[0] === 'string'
        ? <DocumentOrTextList items={value as string[]} fieldKey={fieldKey} variant={referenceVariant} />
        : REFERENCE_FIELDS.includes(fieldKey) && typeof value[0] === 'string'
          ? <ReferenceCard refs={value as string[]} showType={false} showStatus={false} variant={referenceVariant} />
          : <FieldValue fieldKey={fieldKey} value={value} depth={0} locale={locale} />}
    </div>
  );
}

function RelatedMaterialValue({
  fieldKey,
  value,
  locale,
}: {
  fieldKey: string;
  value: unknown[];
  locale: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      {value.map((item, index) => {
        const reference = parseRelatedAssociationValue(item);
        return reference ? (
          <RelatedAssociationRow key={`${fieldKey}-${index}-${reference.ref}`} fieldKey={fieldKey} reference={reference} locale={locale} />
        ) : (
          <FieldValue key={`${fieldKey}-${index}`} fieldKey={fieldKey} value={item} depth={0} locale={locale} />
        );
      })}
    </div>
  );
}

function parseRelatedAssociationValue(item: unknown): RelatedAssociationValue | null {
  if (typeof item === 'string') return { ref: item };
  if (!item || typeof item !== 'object') return null;
  const record = item as Record<string, unknown>;
  if (typeof record.ref !== 'string' || record.ref.trim().length === 0) return null;
  return {
    ref: record.ref,
    title: typeof record.title === 'string' && record.title.trim() ? record.title : undefined,
    summary: typeof record.summary === 'string' && record.summary.trim() ? record.summary : undefined,
  };
}

function RelatedAssociationRow({ fieldKey, reference, locale }: { fieldKey: string; reference: RelatedAssociationValue; locale: string }) {
  const { t } = useI18n();
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const [objectInfo, setObjectInfo] = useState<{ type: string; title: string; path: string } | null>(null);
  const [objectMissing, setObjectMissing] = useState(false);
  const value = reference.ref;
  const objectType = parseRefType(value);
  const objectColor = objectType ? (CATEGORY_COLORS[objectType] || CATEGORY_COLORS.other) : CATEGORY_COLORS.other;
  const isExternal = value.startsWith('http://') || value.startsWith('https://');
  const isDocPreview = DOC_LINK_FIELDS.includes(fieldKey) && isPreviewablePathForField(fieldKey, value);
  const previewDocPath = isDocPreview ? getPreviewableDocPath(value) : value;
  const fallbackTitle = objectType
    ? (locale === 'en' ? 'Loading' : '读取中')
    : value;
  const displayTitle = reference.title || objectInfo?.title || (objectMissing ? value : fallbackTitle);
  const copyValue = objectType ? objectInfo?.path : value;
  const copyLabel = objectType
    ? t('common.copyObjectPath')
    : isExternal
      ? t('common.copyUrl')
      : isDocPreview
        ? t('common.copyDocPath')
        : t('common.copyReference');
  const copiedLabel = objectType
    ? t('common.copiedObjectPath')
    : isExternal
      ? t('common.copiedUrl')
      : isDocPreview
        ? t('common.copiedDocPath')
        : t('common.copiedReference');
  const previewLabel = locale === 'en' ? 'Open in reading panel' : '扩展阅读';
  const isCurrentPanelOpen = Boolean(
    panelOpen && (
      (objectType && panelContent?.type === 'object' && panelContent.objectType === objectType && panelContent.objectId === value)
      || (isExternal && panelContent?.type === 'web' && panelContent.url === value)
      || (!isExternal && isDocPreview && panelContent?.type === 'doc' && panelContent.docPath === previewDocPath)
      || (!isDocPreview && !objectType && panelContent?.type === 'doc' && panelContent.title === value)
    )
  );
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;

  useEffect(() => {
    if (!objectType) {
      setObjectInfo(null);
      setObjectMissing(false);
      return;
    }

    let cancelled = false;
    setObjectInfo(null);
    setObjectMissing(false);
    fetchObjectDetail(objectType, value)
      .then((detail) => {
        if (cancelled) return;
        const obj = detail.data;
        const title = (locale === 'en'
          ? ((obj.title_en as string) || obj.title as string)
          : ((obj.title_zh as string) || obj.title as string)) || value;
        setObjectInfo({ type: objectType, title, path: String(obj.path || detail.target || '') });
      })
      .catch(() => {
        if (!cancelled) setObjectMissing(true);
      });

    return () => {
      cancelled = true;
    };
  }, [locale, objectType, value]);

  const openRelatedPreview = () => {
    if (objectType) {
      openPanel({ type: 'object', title: displayTitle, objectType, objectId: value });
      return;
    }
    if (isExternal) {
      openPanel({ type: 'web', title: displayTitle, url: value });
      return;
    }
    if (isDocPreview) {
      openPanel({ type: 'doc', title: displayTitle, docPath: previewDocPath });
      return;
    }
    openPanel({ type: 'doc', title: displayTitle, data: reference.summary ? `${displayTitle}\n\n${reference.summary}\n\n${value}` : value });
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    openRelatedPreview();
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={openRelatedPreview}
      onKeyDown={handleKeyDown}
      title={previewLabel}
      className="ldvh-body group flex min-h-10 w-full cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50"
    >
      {objectType ? (
        <ObjectTypeIcon type={objectType} size={13} className="shrink-0" style={{ color: objectColor }} />
      ) : isExternal ? (
        <ExternalLink size={13} className="shrink-0 text-ldvh-accent" />
      ) : (
        <FileText size={13} className="shrink-0 text-ldvh-accent" />
      )}
      <div className="min-w-0 flex-1">
        <div className="ldvh-meta-primary truncate">{displayTitle}</div>
        {reference.summary && (
          <div className="ldvh-caption mt-1 line-clamp-2 text-ldvh-text-secondary/70">{reference.summary}</div>
        )}
      </div>
      <div className="flex h-7 shrink-0 items-center gap-1">
        <CopyPathButton path={copyValue} label={copyLabel} copiedLabel={copiedLabel} />
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            openRelatedPreview();
          }}
          title={previewLabel}
          aria-label={previewLabel}
          className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-transparent bg-transparent text-ldvh-text-secondary/70 transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-accent focus-visible:border-ldvh-accent/50 focus-visible:outline-none"
        >
          <PanelIcon size={16} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

function getMaterialLabel(fieldKey: string, locale: string) {
  const labels: Record<string, { zh: string; en: string }> = {
    related_docs: { zh: '文档', en: 'Docs' },
    related_adrs: { zh: '决策', en: 'ADRs' },
    related_sparks: { zh: '火花', en: 'Sparks' },
    related_pitfalls: { zh: '经验', en: 'Pitfalls' },
    related_rules: { zh: '规范', en: 'Specs' },
    urls: { zh: '网址', en: 'URLs' },
    related_workcases: { zh: '工作', en: 'Work Cases' },
    aggregated_execution_refs: { zh: '执行引用', en: 'Execution Refs' },
  };
  const entry = labels[fieldKey];
  if (!entry) return getFieldLabel(fieldKey, locale);
  return locale === 'en' ? entry.en : entry.zh;
}

export function hasDetailContent(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === 'string') return value.trim().length > 0;
  return value !== null && value !== undefined;
}

interface ParsedChecklistItem {
  checked: boolean;
  text: string;
}

function parseDetailChecklist(value: unknown): ParsedChecklistItem[] {
  if (typeof value !== 'string') return [];
  return value
    .split('\n')
    .map((line) => line.match(/^\s*- \[([ xX])\]\s*(.*)/))
    .filter((match): match is RegExpMatchArray => Boolean(match))
    .map((match) => ({ checked: match[1].toLowerCase() === 'x', text: match[2].trim() }));
}

function getChecklistProgress(value: unknown) {
  const items = parseDetailChecklist(value);
  const done = items.filter((item) => item.checked).length;
  return {
    items,
    done,
    total: items.length,
    complete: items.length > 0 && done === items.length,
  };
}

export function WorkCaseReadingLayout({
  obj,
  summary,
  loading,
  locale,
  getStatus,
}: {
  obj: Record<string, unknown>;
  summary: ObjectItem | null;
  loading: boolean;
  locale: string;
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const ownExecutionItems = getWorkCaseExecutionItems(obj);
  const executionItems = sortWorkCaseExecutionItems(
    ownExecutionItems.length > 0 ? ownExecutionItems : (summary?.executionItems ?? [])
  );
  const isExecutionLoading = loading && ownExecutionItems.length === 0;
  const relatedDocs = ((obj.aggregated_related_docs as string[] | undefined) ?? (obj.related_docs as string[] | undefined)) || [];
  const relatedAdrs = ((obj.aggregated_related_adrs as string[] | undefined) ?? (obj.related_adrs as string[] | undefined)) || [];
  const relatedSparks = ((obj.aggregated_related_sparks as string[] | undefined) ?? (obj.related_sparks as string[] | undefined)) || [];
  const relatedPitfalls = ((obj.aggregated_related_pitfalls as string[] | undefined) ?? (obj.related_pitfalls as string[] | undefined)) || [];
  const hidden = new Set([
    ...META_KEYS,
    'goal',
    'priority',
    'description',
    'success_criteria',
    'source',
    'orchestration',
    'verification_evidence',
    'closure_evidence',
    'plan_confirmed_at',
    'closure_requested_at',
    'review_requested_at',
    'closed_at',
    'closure_outcome',
    'residual_risks',
    'followup_refs',
    'revision_history',
    'related_docs',
    'related_adrs',
    'related_sparks',
    'related_pitfalls',
    'related_workcases',
    'aggregated_execution_refs',
    'aggregated_related_docs',
    'aggregated_related_adrs',
    'aggregated_related_sparks',
    'aggregated_related_pitfalls',
  ]);
  const otherEntries = Object.entries(obj).filter(([key, value]) => !hidden.has(key) && hasDetailContent(value));

  return (
    <div className="mb-6 flex flex-col gap-5">
      <WorkCaseHumanOverviewSection
        obj={obj}
        summary={summary}
        executionItems={executionItems}
        locale={locale}
      />

      <WorkCaseLifecycleSection
        obj={obj}
        summary={summary}
        executionItems={executionItems}
        getStatus={getStatus}
      />

      <WorkCaseEvidenceSummarySection obj={obj} summary={summary} />

      <DetailSection title={t('objectDetail.workcaseExecution')} tone="default">
        {isExecutionLoading ? (
          <LoadingHint text={t('objectDetail.executionItemsLoading')} />
        ) : executionItems.length > 0 ? (
          <div className="flex min-w-0 flex-col gap-3">
            <ExecutionFlowBar items={executionItems} t={t} getStatus={getStatus} />
            <div className="divide-y divide-ldvh-border/60 rounded-md border border-ldvh-border bg-ldvh-bg p-2">
              {executionItems.map((item) => (
                <ExecutionItemRow
                  key={item.id}
                  item={item}
                  locale={locale}
                  getStatus={getStatus}
                />
              ))}
            </div>
          </div>
        ) : (
          <EmptyHint text={t('objectList.noExecutionItems')} />
        )}
      </DetailSection>

      <DetailSection title={getFieldLabel('success_criteria', locale)} tone="checklist">
        {hasDetailContent(obj.success_criteria) ? <ChecklistCard value={String(obj.success_criteria)} /> : <EmptyHint text={t('objectDetail.noSuccessCriteria')} />}
      </DetailSection>
      <DetailSection title={getFieldLabel('verification_evidence', locale)} tone="evidence">
        {hasDetailContent(obj.verification_evidence) ? <EvidenceBlock value={String(obj.verification_evidence)} embedded /> : <EmptyHint text={t('objectDetail.noVerificationEvidence')} />}
      </DetailSection>
      <DetailSection title={getFieldLabel('closure_evidence', locale)} tone="evidence">
        {hasDetailContent(obj.closure_evidence) ? <EvidenceBlock value={String(obj.closure_evidence)} embedded /> : <EmptyHint text={t('objectDetail.noClosureEvidenceForWorkCase')} />}
      </DetailSection>

      <WorkCaseAiContextSection obj={obj} locale={locale} />

      <RelatedContentSection
        entries={sortRelatedContentEntries([
          ['related_workcases', obj.related_workcases],
          ['related_docs', relatedDocs],
          ['related_adrs', relatedAdrs],
          ['related_sparks', relatedSparks],
          ['related_pitfalls', relatedPitfalls],
        ].filter((entry): entry is RelatedContentEntry => Array.isArray(entry[1]) && hasDetailContent(entry[1])))}
        locale={locale}
      />

      {otherEntries.length > 0 && (
        <DetailSection title={t('objectDetail.otherFields')} tone="default">
          <div className="flex flex-col gap-3">
            {otherEntries.map(([key, value]) => (
              <ContentField key={key} fieldKey={key} value={value} locale={locale} objType="workcase" />
            ))}
          </div>
        </DetailSection>
      )}
    </div>
  );
}

type WorkCaseLifecycleTone = 'draft' | 'planReview' | 'planConfirming' | 'active' | 'blocked' | 'verification' | 'resultReview' | 'review' | 'closed';

const workCaseLifecycleClass: Record<WorkCaseLifecycleTone, string> = {
  draft: 'border-sky-500/25 bg-sky-500/10 text-sky-400',
  planReview: 'border-sky-500/25 bg-sky-500/10 text-sky-400',
  planConfirming: 'border-violet-500/25 bg-violet-500/10 text-violet-400',
  active: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400',
  blocked: 'border-amber-500/30 bg-amber-500/10 text-amber-400',
  verification: 'border-blue-500/25 bg-blue-500/10 text-blue-400',
  resultReview: 'border-indigo-500/25 bg-indigo-500/10 text-indigo-400',
  review: 'border-violet-500/25 bg-violet-500/10 text-violet-400',
  closed: 'border-zinc-500/25 bg-zinc-500/10 text-zinc-400',
};

function WorkCaseLifecycleSection({
  obj,
  summary,
  executionItems,
  getStatus,
}: {
  obj: Record<string, unknown>;
  summary: ObjectItem | null;
  executionItems: RelatedObjectSummary[];
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const rawStatus = detailString(obj.status, detailString(summary?.status, 'unknown'));
  const lifecycle = getWorkCaseLifecycle(obj, summary, executionItems);
  const checklistProgress = getChecklistProgress(obj.success_criteria);
  const successCriteriaTotal = summary?.successCriteriaTotal ?? checklistProgress.total;
  const successCriteriaDone = summary?.successCriteriaDone ?? checklistProgress.done;
  const executionTotal = summary?.executionItemTotal ?? executionItems.length;
  const executionDone = summary?.executionItemDone ?? executionItems.filter((item) => item.status === 'done').length;
  const recordItems = [
    { label: t('objectList.planConfirmedAt'), recorded: Boolean(summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at)) },
    { label: t('objectList.closureRequestedAt'), recorded: Boolean(summary?.hasClosureRequestedAt ?? (hasDetailContent(obj.closure_requested_at) || hasDetailContent(obj.review_requested_at))) },
    { label: t('objectList.verificationEvidence'), recorded: Boolean(summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence)) },
    { label: t('objectList.closureEvidence'), recorded: Boolean(summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence)) },
    ...(rawStatus === 'closed'
      ? [{ label: t('objectList.closedAt'), recorded: Boolean(summary?.hasClosedAt ?? hasDetailContent(obj.closed_at)) }]
      : []),
  ];

  return (
    <DetailSection title={t('objectDetail.workcaseProgress')} tone="default">
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
          <div className="ldvh-caption-strong mb-2 text-ldvh-text-secondary">{t('objectDetail.lifecycleStage')}</div>
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className={`ldvh-caption-strong inline-flex rounded-md border px-2 py-1 ${workCaseLifecycleClass[lifecycle.tone]}`}>
              {t(lifecycle.labelKey)}
            </span>
            <span className="ldvh-meta-muted">{getStatus(rawStatus)}</span>
          </div>
        </div>
        <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <ProgressMetric
              label={t('objectDetail.successCriteriaProgress')}
              done={successCriteriaDone}
              total={successCriteriaTotal}
              emptyText={t('objectDetail.noSuccessCriteria')}
            />
            <ProgressMetric
              label={t('objectDetail.executionItemProgress')}
              done={executionDone}
              total={executionTotal}
              emptyText={t('objectList.noExecutionItems')}
            />
          </div>
          {executionItems.length > 0 && (
            <div className="mt-3">
              <ExecutionFlowBar items={executionItems} t={t} getStatus={getStatus} compact />
            </div>
          )}
        </div>
      </div>
      <div className="mt-3 flex min-w-0 flex-wrap gap-2">
        {recordItems.map((item) => (
          <DetailRecordItem key={item.label} label={item.label} recorded={item.recorded} />
        ))}
      </div>
    </DetailSection>
  );
}

function ProgressMetric({
  label,
  done,
  total,
  emptyText,
}: {
  label: string;
  done: number;
  total: number;
  emptyText: string;
}) {
  const ratio = total > 0 ? Math.max(0, Math.min(100, (done / total) * 100)) : 0;
  return (
    <div className="min-w-0">
      <div className="mb-1.5 flex min-w-0 items-center justify-between gap-2">
        <span className="ldvh-caption-strong min-w-0 truncate text-ldvh-text-secondary">{label}</span>
        <span className="ldvh-caption shrink-0 text-ldvh-text-secondary">{total > 0 ? `${done}/${total}` : emptyText}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-ldvh-border/45">
        <div className="h-full rounded-full bg-ldvh-accent" style={{ width: `${ratio}%` }} />
      </div>
    </div>
  );
}

function WorkCaseHumanOverviewSection({
  obj,
  summary,
  executionItems,
  locale,
}: {
  obj: Record<string, unknown>;
  summary: ObjectItem | null;
  executionItems: RelatedObjectSummary[];
  locale: string;
}) {
  const { t } = useI18n();
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const goal = detailString(obj.goal);
  const description = detailString(obj.description);
  const priority = detailString(obj.priority) || detailString(summary?.priority);
  const checklistProgress = getChecklistProgress(obj.success_criteria);
  const successCriteriaTotal = summary?.successCriteriaTotal ?? checklistProgress.total;
  const successCriteriaDone = summary?.successCriteriaDone ?? checklistProgress.done;
  const executionTotal = summary?.executionItemTotal ?? executionItems.length;
  const executionDone = summary?.executionItemDone ?? executionItems.filter((item) => item.status === 'done').length;
  const lifecycle = getWorkCaseLifecycle(obj, summary, executionItems);
  const humanGateLabel = lifecycle.tone === 'planConfirming'
    ? t('objectDetail.humanPlanConfirmation')
    : lifecycle.tone === 'review' || lifecycle.tone === 'closed'
      ? t('objectDetail.humanClosureConfirmation')
      : t('objectDetail.humanGateTip');
  const summaryItems = [
    { label: t('objectDetail.successCriteriaProgress'), value: successCriteriaTotal > 0 ? `${successCriteriaDone}/${successCriteriaTotal}` : '—' },
    { label: t('objectDetail.executionItemProgress'), value: executionTotal > 0 ? `${executionDone}/${executionTotal}` : '—' },
    { label: t('objectDetail.closeDecisionRecordState'), value: summarizeRecordState(obj, summary, executionItems, t) },
  ];

  return (
    <ReadingNodeSection
      title={t('objectDetail.workcaseHumanOverview')}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="flex flex-col gap-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-4">
            <div className="mb-2 flex min-w-0 flex-wrap items-center gap-2">
              <span className="ldvh-caption-strong rounded-md border border-emerald-500/25 bg-emerald-500/10 px-2 py-1 text-emerald-400">
                {t('objectDetail.workcaseHumanContext')}
              </span>
              {priority && <span className="ldvh-chip rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1 text-ldvh-text-secondary">{priority}</span>}
              <span className="ldvh-chip rounded-md border border-violet-500/25 bg-violet-500/10 px-2 py-1 text-violet-400">{humanGateLabel}</span>
            </div>
            {hasDetailContent(goal) ? (
              <SummaryText value={goal} collapseThreshold={900} />
            ) : (
              <EmptyHint text={t('objectDetail.noPlanGoal')} />
            )}
            <div className="mt-3 border-t border-ldvh-border/70 pt-3">
              <div className="ldvh-caption-strong mb-1 text-ldvh-text-secondary">{t('objectDetail.planDescription')}</div>
              {hasDetailContent(description) ? (
                <SummaryText value={description} collapseThreshold={900} />
              ) : (
                <EmptyHint text={t('objectDetail.noPlanDescription')} />
              )}
            </div>
          </div>
          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-4">
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              {summaryItems.map((item) => (
                <div key={item.label} className="min-w-0 rounded-md border border-ldvh-border/70 bg-ldvh-panel px-3 py-2">
                  <div className="ldvh-caption mb-1 truncate text-ldvh-text-secondary">{item.label}</div>
                  <div className="ldvh-section-title truncate">{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { label: t('objectDetail.lifecycleStage'), value: t(getWorkCaseLifecycle(obj, summary, executionItems).labelKey) },
            { label: t('objectDetail.successCriteriaProgress'), value: successCriteriaTotal > 0 ? `${successCriteriaDone}/${successCriteriaTotal}` : '—' },
            { label: t('objectDetail.executionItemProgress'), value: executionTotal > 0 ? `${executionDone}/${executionTotal}` : '—' },
            { label: t('objectDetail.closeDecisionRecordState'), value: summarizeRecordState(obj, summary, executionItems, t) },
          ].map((item) => (
            <div key={item.label} className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-bg px-3 py-2.5">
              <div className="ldvh-caption mb-1 truncate opacity-85">{item.label}</div>
              <div className="ldvh-section-title truncate">{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </ReadingNodeSection>
  );
}

function WorkCaseEvidenceSummarySection({ obj, summary }: { obj: Record<string, unknown>; summary: ObjectItem | null }) {
  const { t } = useI18n();
  const checklistProgress = getChecklistProgress(obj.success_criteria);
  const successCriteriaTotal = summary?.successCriteriaTotal ?? checklistProgress.total;
  const successCriteriaDone = summary?.successCriteriaDone ?? checklistProgress.done;
  const items = [
    {
      label: t('objectDetail.successCriteriaProgress'),
      value: successCriteriaTotal > 0 ? `${successCriteriaDone}/${successCriteriaTotal}` : '—',
      recorded: successCriteriaTotal > 0,
    },
    {
      label: t('objectList.planConfirmedAt'),
      value: summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at) ? t('objectList.hasRecord') : t('objectList.missingRecord'),
      recorded: Boolean(summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at)),
    },
    {
      label: t('objectDetail.verificationEvidence'),
      value: summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence) ? t('objectList.hasRecord') : t('objectList.missingRecord'),
      recorded: Boolean(summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence)),
    },
    {
      label: t('objectDetail.closureEvidence'),
      value: summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence) ? t('objectList.hasRecord') : t('objectList.missingRecord'),
      recorded: Boolean(summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence)),
    },
  ];

  return (
    <DetailSection title={t('objectDetail.closeDecisionRecordState')} tone="default">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <div
            key={item.label}
            className={`min-w-0 rounded-lg border px-3 py-2.5 ${
              item.recorded
                ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
            }`}
          >
            <div className="ldvh-caption mb-1 truncate opacity-85">{item.label}</div>
            <div className="ldvh-section-title truncate">{item.value}</div>
          </div>
        ))}
      </div>
    </DetailSection>
  );
}

function WorkCaseAiContextSection({ obj, locale }: { obj: Record<string, unknown>; locale: string }) {
  const { t } = useI18n();
  const [state, setState] = useState<ReadingNodeState>('collapsed');
  const orchestration = getWorkCaseOrchestration(obj);
  const aiEntries: Array<[string, unknown]> = [
    ['orchestration', obj.orchestration],
    ['plan_confirmed_at', obj.plan_confirmed_at],
    ['closure_requested_at', obj.closure_requested_at ?? obj.review_requested_at],
    ['closed_at', obj.closed_at],
    ['closure_outcome', obj.closure_outcome],
    ['residual_risks', obj.residual_risks],
    ['followup_refs', obj.followup_refs],
    ['revision_history', orchestration.revision_history],
    ['source', obj.source],
  ].filter((entry): entry is [string, unknown] => hasDetailContent(entry[1]));

  const executionRefs = detailStringArray(obj.aggregated_execution_refs);

  return (
    <ReadingNodeSection
      title={t('objectDetail.workcaseAiContext')}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="flex flex-col gap-4">
        {aiEntries.length > 0 && (
          <div className="rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">{t('objectDetail.workcaseAiCore')}</div>
            <div className="flex flex-col gap-2">
              {aiEntries.map(([fieldKey, value]) => (
                <ContentField key={fieldKey} fieldKey={fieldKey} value={value} locale={locale} objType="workcase" />
              ))}
            </div>
          </div>
        )}

        <WorkCaseReviewSection orchestration={orchestration} />

        {executionRefs.length > 0 && (
          <div className="rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">{t('objectDetail.executionReferences')}</div>
            <StringList items={executionRefs} />
          </div>
        )}
      </div>
    </ReadingNodeSection>
  );
}

function summarizeRecordState(obj: Record<string, unknown>, summary: ObjectItem | null, executionItems: RelatedObjectSummary[], t: (key: string) => string) {
  const planConfirmed = Boolean(summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at));
  const verificationRecorded = Boolean(summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence));
  const closureRecorded = Boolean(summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence));
  const closureRequested = Boolean(summary?.hasClosureRequestedAt ?? (hasDetailContent(obj.closure_requested_at) || hasDetailContent(obj.review_requested_at)));
  const closedAtRecorded = Boolean(summary?.hasClosedAt ?? hasDetailContent(obj.closed_at));
  const blockedCount = executionItems.filter((item) => item.status === 'blocked' || Boolean(item.blockingReason)).length;
  const items = [
    planConfirmed ? t('objectList.planConfirmedAt') : null,
    verificationRecorded ? t('objectList.verificationEvidence') : null,
    closureRecorded ? t('objectList.closureEvidence') : null,
    closureRequested ? t('objectList.closureRequestedAt') : null,
    closedAtRecorded ? t('objectList.closedAt') : null,
    blockedCount > 0 ? `${blockedCount} ${t('objectDetail.lifecycleBlocked')}` : null,
  ].filter(Boolean);

  if (items.length === 0) return t('objectList.missingRecord');
  return items.slice(0, 3).join(' · ');
}

function getWorkCaseLifecycle(
  obj: Record<string, unknown>,
  summary: ObjectItem | null,
  executionItems: RelatedObjectSummary[],
): { tone: WorkCaseLifecycleTone; labelKey: 'objectDetail.lifecycleDraft' | 'objectDetail.lifecyclePlanReview' | 'objectDetail.lifecyclePlanConfirming' | 'objectDetail.lifecycleActive' | 'objectDetail.lifecycleBlocked' | 'objectDetail.lifecycleVerification' | 'objectDetail.lifecycleResultReview' | 'objectDetail.lifecycleReview' | 'objectDetail.lifecycleClosed' } {
  const status = detailString(obj.status, detailString(summary?.status));
  if (status === 'closed') return { tone: 'closed', labelKey: 'objectDetail.lifecycleClosed' };
  if (status === 'subagents_plan_reviewing') return { tone: 'planReview', labelKey: 'objectDetail.lifecyclePlanReview' };
  if (status === 'human_plan_confirming') return { tone: 'planConfirming', labelKey: 'objectDetail.lifecyclePlanConfirming' };
  if (status === 'human_closure_confirming') return { tone: 'review', labelKey: 'objectDetail.lifecycleReview' };
  if (isWorkCaseResultReviewStatus(status)) return { tone: 'resultReview', labelKey: 'objectDetail.lifecycleResultReview' };
  if (status === 'review_needed') return { tone: 'review', labelKey: 'objectDetail.lifecycleReview' };
  if (executionItems.some((item) => item.status === 'blocked' || Boolean(item.blockingReason))) {
    return { tone: 'blocked', labelKey: 'objectDetail.lifecycleBlocked' };
  }
  if (status === 'draft') return { tone: 'draft', labelKey: 'objectDetail.lifecycleDraft' };
  if (hasDetailContent(obj.verification_evidence) || hasDetailContent(obj.closure_evidence)) {
    return { tone: 'verification', labelKey: 'objectDetail.lifecycleVerification' };
  }
  return { tone: 'active', labelKey: 'objectDetail.lifecycleActive' };
}

function ExecutionItemRow({
  item,
  locale,
  getStatus,
}: {
  item: RelatedObjectSummary;
  locale: string;
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const tone = getExecutionFlowTone(item);
  const flowLabel = getExecutionFlowLabel(item, t, getStatus);
  const toneClass = executionFlowRowClass[tone];

  return (
    <div className={`my-1 rounded-md border px-3 py-2.5 ${toneClass}`}>
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-1.5">
            <ExecutionFlowMarker tone={tone} label={flowLabel} compact />
            <span className="ldvh-body min-w-0 truncate">{getLocalizedTitle(item, locale)}</span>
          </div>
          <div className="mt-0.5 flex min-w-0 flex-wrap gap-x-3 gap-y-1">
            <span className="ldvh-meta-muted">{item.role || item.id}</span>
            {item.mode && <span className="ldvh-caption">{item.mode}</span>}
            <span className="ldvh-caption">{flowLabel}</span>
          </div>
        </div>
      </div>
      {item.expectedOutput && (
        <p className="ldvh-body-muted mt-2 border-l-2 border-ldvh-border/50 pl-2">{item.expectedOutput}</p>
      )}
      {item.resultSummary && (
        <p className="ldvh-body mt-2 border-l-2 border-emerald-500/40 pl-2">{item.resultSummary}</p>
      )}
      {item.blockingReason && (
        <p className="ldvh-body mt-2 border-l-2 border-amber-500/60 pl-2 text-amber-300">{item.blockingReason}</p>
      )}
      {(item.inputRefs?.length || item.evidenceRefs?.length) && (
        <div className="mt-2 flex min-w-0 flex-wrap gap-1.5">
          {[
            ...(item.inputRefs ?? []).map((ref) => ({ kind: 'input', ref })),
            ...(item.evidenceRefs ?? []).map((ref) => ({ kind: 'evidence', ref })),
          ].map(({ kind, ref }, index) => (
            <span key={`${kind}-${index}-${ref}`} className="ldvh-chip max-w-full truncate rounded-md border border-ldvh-border bg-ldvh-bg px-1.5 py-0.5 text-ldvh-text-secondary">
              {ref}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function WorkCaseReviewSection({ orchestration }: { orchestration: Record<string, unknown> }) {
  const { t } = useI18n();
  const planReview = isDetailRecord(orchestration.plan_review) ? orchestration.plan_review : null;
  const resultReview = isDetailRecord(orchestration.result_review) ? orchestration.result_review : null;
  const legacyReview = isDetailRecord(orchestration.review) ? orchestration.review : null;

  if (planReview || resultReview) {
    return (
      <DetailSection title={t('objectDetail.workcaseReview')} tone="default">
        <div className="divide-y divide-ldvh-border/60">
          {planReview && <ReviewRecordGroup title={t('objectDetail.planReview')} review={planReview} phase="plan" />}
          {resultReview && <ReviewRecordGroup title={t('objectDetail.resultReview')} review={resultReview} phase="result" />}
        </div>
      </DetailSection>
    );
  }

  if (!legacyReview) return null;
  return <LegacyWorkCaseReviewSection review={legacyReview} />;
}

function ReviewRecordGroup({
  title,
  review,
  phase,
}: {
  title: string;
  review: Record<string, unknown>;
  phase: 'plan' | 'result';
}) {
  const { t } = useI18n();
  const reviewItems = Array.isArray(review.review_items)
    ? review.review_items.filter((item): item is Record<string, unknown> => isDetailRecord(item))
    : [];
  const controllerSelfCheck = isDetailRecord(review.controller_self_check) ? review.controller_self_check : null;
  const controllerResolution = isDetailRecord(review.controller_resolution) ? review.controller_resolution : null;
  const humanConfirmation = phase === 'plan' && isDetailRecord(review.human_confirmation) ? review.human_confirmation : null;
  const humanClosureConfirmation = phase === 'result' && isDetailRecord(review.human_closure_confirmation) ? review.human_closure_confirmation : null;
  const hasBody = reviewItems.length > 0
    || controllerSelfCheck
    || controllerResolution
    || humanConfirmation
    || humanClosureConfirmation;

  if (!hasBody) return null;

  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">{title}</div>
      <div className="flex min-w-0 flex-col gap-3">
        {controllerSelfCheck && (
          <ReviewInlineField
            label={t('objectDetail.controllerSelfCheck')}
            value={<ReviewRecordSummary record={controllerSelfCheck} />}
            compact
          />
        )}
        {reviewItems.length > 0 && (
          <ReviewInlineField
            label={t('objectDetail.reviewItems')}
            value={<ReviewItemsList items={reviewItems} />}
            compact
          />
        )}
        {controllerResolution && (
          <ReviewInlineField
            label={t('objectDetail.controllerResolution')}
            value={<ReviewRecordSummary record={controllerResolution} />}
            compact
          />
        )}
        {humanConfirmation && (
          <ReviewInlineField
            label={t('objectDetail.humanPlanConfirmation')}
            value={<ReviewRecordSummary record={humanConfirmation} />}
            compact
          />
        )}
        {humanClosureConfirmation && (
          <ReviewInlineField
            label={t('objectDetail.humanClosureConfirmation')}
            value={<ReviewRecordSummary record={humanClosureConfirmation} />}
            compact
          />
        )}
      </div>
    </div>
  );
}

function ReviewItemsList({ items }: { items: Record<string, unknown>[] }) {
  const { getStatus } = useI18n();
  return (
    <div className="flex min-w-0 flex-col gap-2">
      {items.slice(0, 4).map((item, index) => {
        const result = isDetailRecord(item.result) ? item.result : {};
        const status = detailString(result.status);
        const title = [
          detailString(item.agent),
          detailString(item.role),
          detailString(item.phase),
        ].filter(Boolean).join(' · ') || `#${index + 1}`;
        const summary = detailString(result.summary) || detailString(item.summary);
        return (
          <div key={`${title}-${index}`} className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg px-2.5 py-2">
            <div className="mb-1 flex min-w-0 flex-wrap items-center gap-2">
              <span className="ldvh-caption-strong min-w-0 truncate text-ldvh-text">{title}</span>
              {status && (
                <span className="ldvh-chip rounded-md border border-ldvh-border px-1.5 py-0.5 text-ldvh-text-secondary">
                  {getStatus(status)}
                </span>
              )}
            </div>
            {summary && <SummaryText value={summary} collapseThreshold={220} />}
          </div>
        );
      })}
      {items.length > 4 && (
        <span className="ldvh-caption text-ldvh-text-secondary">+{items.length - 4}</span>
      )}
    </div>
  );
}

function ReviewRecordSummary({ record }: { record: Record<string, unknown> }) {
  const { getStatus } = useI18n();
  const result = isDetailRecord(record.result) ? record.result : {};
  const status = detailString(result.status) || detailString(record.decision);
  const summary = detailString(record.summary)
    || detailString(result.summary)
    || detailString(record.scope)
    || detailString(record.notes);
  const at = detailString(record.confirmed_at) || detailString(record.signed_at);

  return (
    <div className="min-w-0">
      <div className="mb-1 flex min-w-0 flex-wrap items-center gap-2">
        {status && (
          <span className="ldvh-chip rounded-md border border-ldvh-border px-1.5 py-0.5 text-ldvh-text-secondary">
            {getStatus(status)}
          </span>
        )}
        {at && <span className="ldvh-meta-muted">{formatDateTime(at)}</span>}
      </div>
      {summary ? <SummaryText value={summary} collapseThreshold={320} /> : <span className="ldvh-body-muted">-</span>}
    </div>
  );
}

function LegacyWorkCaseReviewSection({ review }: { review: Record<string, unknown> }) {
  const { t } = useI18n();

  const specialistReview = isDetailRecord(review.specialist_review) ? review.specialist_review : null;
  const hasSpecialistDetail = Boolean(
    specialistReview && (
      hasDetailContent(specialistReview.required)
      || hasDetailContent(specialistReview.role)
      || hasDetailContent(specialistReview.expected_output)
    )
  );

  return (
    <DetailSection title={t('objectDetail.workcaseReview')} tone="default">
      <div className="divide-y divide-ldvh-border/60">
        {hasDetailContent(review.controller_self_check) && (
          <ReviewInlineField
            label={t('objectDetail.controllerSelfCheck')}
            value={<ReviewBoolean value={review.controller_self_check} />}
          />
        )}
        {hasSpecialistDetail && specialistReview && (
          <div className="py-3 first:pt-0 last:pb-0">
            <div className="ldvh-caption-strong mb-2 text-ldvh-text-secondary">{t('objectDetail.specialistReview')}</div>
            <div className="flex flex-col gap-2">
              {hasDetailContent(specialistReview.required) && (
                <ReviewInlineField
                  label={t('objectDetail.reviewRequirement')}
                  value={<ReviewBoolean value={specialistReview.required} />}
                  compact
                />
              )}
              {hasDetailContent(specialistReview.role) && (
                <ReviewInlineField
                  label={t('objectDetail.reviewRole')}
                  value={<span className="ldvh-body">{String(specialistReview.role)}</span>}
                  compact
                />
              )}
              {hasDetailContent(specialistReview.expected_output) && (
                <ReviewInlineField
                  label={t('objectDetail.expectedOutput')}
                  value={<SummaryText value={String(specialistReview.expected_output)} collapseThreshold={360} />}
                  compact
                />
              )}
            </div>
          </div>
        )}
        {hasDetailContent(review.human_closure_review) && (
          <ReviewInlineField
            label={t('objectDetail.humanClosureReview')}
            value={<ReviewBoolean value={review.human_closure_review} />}
          />
        )}
      </div>
    </DetailSection>
  );
}

function ReviewInlineField({ label, value, compact = false }: { label: string; value: ReactNode; compact?: boolean }) {
  return (
    <div className={`grid gap-2 ${compact ? 'sm:grid-cols-[5.25rem_1fr]' : 'py-3 first:pt-0 last:pb-0 sm:grid-cols-[6.25rem_1fr]'}`}>
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{label}</div>
      <div className="min-w-0">{value}</div>
    </div>
  );
}

function ReviewBoolean({ value }: { value: unknown }) {
  const { t } = useI18n();
  const enabled = value === true || value === 'true' || value === 'required';
  return (
    <span className={`ldvh-chip inline-flex rounded-md border px-2 py-0.5 ${
      enabled
        ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400'
        : 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary'
    }`}
    >
      {enabled ? t('objectDetail.required') : t('objectDetail.notRequired')}
    </span>
  );
}

export function DetailRecordItem({ label, recorded }: { label: string; recorded: boolean }) {
  const { t } = useI18n();
  return (
    <span className={`ldvh-caption-strong inline-flex items-center gap-1.5 rounded-md border px-2 py-1 ${
      recorded
        ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400'
        : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
    }`}
    >
      <span>{label}</span>
      <span className="ldvh-meta-muted">{recorded ? t('objectList.hasRecord') : t('objectList.missingRecord')}</span>
    </span>
  );
}

const ADR_READING_NODES: Array<{ field: string; zh: string; en: string }> = [
  { field: 'context', zh: '背景', en: 'Context' },
  { field: 'decision', zh: '决策', en: 'Decision' },
  { field: 'consequences', zh: '影响', en: 'Consequences' },
  { field: 'archive_reason', zh: '归档原因', en: 'Archive Reason' },
  { field: 'deprecated_reason', zh: '废弃原因', en: 'Deprecated Reason' },
];

export function AdrReadingLayout({
  obj,
  relatedEntries,
  locale,
}: {
  obj: Record<string, unknown>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-5">
      {ADR_READING_NODES.map((node) => (
        <AdrReadingNode
          key={node.field}
          title={locale === 'en' ? node.en : node.zh}
          value={obj[node.field]}
          locale={locale}
        />
      ))}
      <RelatedContentSection entries={relatedEntries} locale={locale} />
    </div>
  );
}

function AdrReadingNode({
  title,
  value,
  locale,
}: {
  title: string;
  value: unknown;
  locale: string;
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  if (!hasDetailContent(value)) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <StudyTextNodeContent value={value} />
    </ReadingNodeSection>
  );
}

const PITFALL_READING_NODES: Array<{ field: string; zh: string; en: string; kind?: 'evidence' }> = [
  { field: 'symptoms', zh: '现象', en: 'Symptoms' },
  { field: 'trigger_conditions', zh: '触发', en: 'Triggers' },
  { field: 'root_cause', zh: '根因', en: 'Root Cause' },
  { field: 'resolution', zh: '方案', en: 'Resolution' },
  { field: 'verification', zh: '验证', en: 'Verification', kind: 'evidence' },
  { field: 'avoidance', zh: '规避', en: 'Avoidance' },
  { field: 'applicability', zh: '范围', en: 'Scope' },
  { field: 'archive_reason', zh: '归档原因', en: 'Archive Reason' },
  { field: 'notes', zh: '备注', en: 'Notes' },
];

export function PitfallReadingLayout({
  obj,
  relatedEntries,
  locale,
}: {
  obj: Record<string, unknown>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
}) {
  const sourceSparkEntries: RelatedContentEntry[] = Array.isArray(obj.source_sparks) && hasDetailContent(obj.source_sparks)
    ? [['source_sparks', obj.source_sparks]]
    : [];
  const allRelatedEntries = sortRelatedContentEntries([...sourceSparkEntries, ...relatedEntries]);

  return (
    <div className="mb-6 flex flex-col gap-5">
      {PITFALL_READING_NODES.map((node) => (
        <PitfallReadingNode
          key={node.field}
          title={locale === 'en' ? node.en : node.zh}
          value={obj[node.field]}
          locale={locale}
          kind={node.kind}
        />
      ))}
      <RelatedContentSection entries={allRelatedEntries} locale={locale} />
    </div>
  );
}

function PitfallReadingNode({
  title,
  value,
  locale,
  kind,
}: {
  title: string;
  value: unknown;
  locale: string;
  kind?: 'evidence';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  if (!hasDetailContent(value)) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      {kind === 'evidence' ? (
        <EvidenceReadingNodes value={String(value)} />
      ) : (
        <PitfallTextNodeContent value={value} />
      )}
    </ReadingNodeSection>
  );
}

function PitfallTextNodeContent({ value }: { value: unknown }) {
  return (
    <div className="ldvh-study-node-content">
      <div className="ldvh-inline-markdown max-w-none">
        <Markdown remarkPlugins={[remarkGfm]}>{String(value)}</Markdown>
      </div>
    </div>
  );
}

const SPARK_READING_NODES: Array<{ field: string; zh: string; en: string; kind: 'summary' | 'intent' | 'evolution' | 'routing' }> = [
  { field: 'source_detail', zh: '意图', en: 'Intent', kind: 'intent' },
  { field: 'description', zh: '摘要', en: 'Current Summary', kind: 'summary' },
  { field: 'evolution', zh: '演变', en: 'Evolution', kind: 'evolution' },
  { field: 'routing', zh: '分流', en: 'Routing', kind: 'routing' },
];
type SparkEvolutionEntry = { key: string; at?: string; summary: string };

export function SparkReadingLayout({
  obj,
  relatedEntries,
  locale,
}: {
  obj: Record<string, unknown>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-5">
      {SPARK_READING_NODES.map((node) => (
        <SparkReadingNode
          key={node.field}
          title={locale === 'en' ? node.en : node.zh}
          obj={obj}
          locale={locale}
          kind={node.kind}
        />
      ))}
      <RelatedContentSection entries={relatedEntries} locale={locale} />
    </div>
  );
}

function SparkReadingNode({
  title,
  obj,
  locale,
  kind,
}: {
  title: string;
  obj: Record<string, unknown>;
  locale: string;
  kind: 'summary' | 'intent' | 'evolution' | 'routing';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const hasContent = kind === 'summary'
    ? hasDetailContent(obj.description)
    : kind === 'intent'
      ? hasDetailContent(obj.source_detail)
    : kind === 'evolution'
      ? hasDetailContent(obj.evolution)
      : hasSparkRoutingContent(obj);

  if (!hasContent) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      {kind === 'summary' && <SparkSummaryNode value={obj.description} />}
      {kind === 'intent' && <SparkSummaryNode value={obj.source_detail} />}
      {kind === 'evolution' && <SparkEvolutionNode value={obj.evolution} locale={locale} />}
      {kind === 'routing' && <SparkRoutingNode obj={obj} locale={locale} />}
    </ReadingNodeSection>
  );
}

function SparkSummaryNode({ value }: { value: unknown }) {
  return <StudyTextNodeContent value={value} />;
}

function SparkEvolutionNode({ value, locale }: { value: unknown; locale: string }) {
  if (!Array.isArray(value)) return <StudyTextNodeContent value={value} />;
  const entries = value
    .map((item, index) => parseSparkEvolutionEntry(item, index))
    .filter((entry): entry is SparkEvolutionEntry => Boolean(entry))
    .reverse();

  if (entries.length === 0) return null;

  return (
    <div className="flex min-w-0 flex-col gap-2">
      {entries.map((entry) => (
        <div key={entry.key} className="min-w-0 rounded-md border border-ldvh-border/45 bg-ldvh-bg/45 px-3 py-2">
          <div className="mb-1.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-accent" aria-hidden="true" />
            <SparkEvolutionTime value={entry.at} locale={locale} />
          </div>
          <StudyTextNodeContent value={entry.summary} compact />
        </div>
      ))}
    </div>
  );
}

function parseSparkEvolutionEntry(item: unknown, index: number): SparkEvolutionEntry | null {
  if (typeof item === 'string' && item.trim().length > 0) {
    return { key: `${index}-${item}`, summary: item };
  }
  if (!item || typeof item !== 'object') return null;
  const record = item as Record<string, unknown>;
  const summary = typeof record.summary === 'string' ? record.summary.trim() : '';
  if (!summary) return null;
  return {
    key: `${index}-${String(record.at ?? summary)}`,
    at: typeof record.at === 'string' ? record.at : undefined,
    summary,
  };
}

function SparkEvolutionTime({ value, locale }: { value?: string; locale: string }) {
  if (!value) {
    return (
      <div className="ldvh-caption-strong min-w-0 break-words text-ldvh-text-secondary">
        {locale === 'en' ? 'Evolution' : '演变'}
      </div>
    );
  }
  const [date, time] = formatDateTime(value).split(' ');
  return (
    <div className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-0.5 font-mono tabular-nums">
      <span className="ldvh-caption-strong min-w-0 break-words text-ldvh-text-secondary">{date}</span>
      {time && <span className="ldvh-meta-muted min-w-0 break-words leading-4">{time}</span>}
    </div>
  );
}

function SparkRoutingNode({ obj, locale }: { obj: Record<string, unknown>; locale: string }) {
  const status = String(obj.status ?? 'pending');
  const statusLabel = getObjectStatusLocale('spark', status, locale);
  const resolvedRef = getSparkResolvedReference(obj.resolved_to);
  const resolvedAt = typeof obj.resolved_at === 'string' && obj.resolved_at.trim().length > 0 ? obj.resolved_at : null;
  const discardReason = typeof obj.discard_reason === 'string' && obj.discard_reason.trim().length > 0 ? obj.discard_reason : null;

  return (
    <div className="flex flex-col divide-y divide-ldvh-border/60">
      <DetailInlineField
        label={locale === 'en' ? 'Status' : '状态'}
        value={<StatusBadge status={status} statusLabel={statusLabel} objectType="spark" size="sm" />}
      />
      {resolvedRef && (
        <DetailObjectRow
          label={locale === 'en' ? 'Target' : '目标'}
          fallbackId={resolvedRef.ref}
          objectType={resolvedRef.objectType}
          locale={locale}
          variant="property"
        />
      )}
      {resolvedAt && (
        <DetailInlineField
          label={locale === 'en' ? 'Routed At' : '分流时间'}
          value={<span className="ldvh-definition-text">{formatDateTime(resolvedAt)}</span>}
        />
      )}
      {discardReason && (
        <DetailInlineField
          label={locale === 'en' ? 'Discard Reason' : '废弃原因'}
          value={<StudyTextNodeContent value={discardReason} />}
        />
      )}
    </div>
  );
}

function hasSparkRoutingContent(obj: Record<string, unknown>) {
  const status = String(obj.status ?? 'pending');
  return status === 'resolved'
    || status === 'discarded'
    || hasDetailContent(obj.resolved_to)
    || hasDetailContent(obj.resolved_at)
    || hasDetailContent(obj.discard_reason);
}

function getSparkResolvedReference(value: unknown): { ref: string; objectType: string } | null {
  if (typeof value === 'string') {
    const ref = value.trim();
    if (!ref) return null;
    const objectType = getObjectRefType(ref);
    return objectType ? { ref, objectType } : null;
  }
  if (!value || typeof value !== 'object') return null;
  const record = value as Record<string, unknown>;
  const ref = typeof record.ref === 'string' ? record.ref.trim() : '';
  if (!ref) return null;
  const type = typeof record.type === 'string' ? record.type.trim() : '';
  const objectType = type || getObjectRefType(ref);
  return objectType ? { ref, objectType } : null;
}

const EVIDENCE_NODE_ORDER = ['验证计划', '验证命令', '验证结果', '结论'];

function EvidenceReadingNodes({ value }: { value: string }) {
  const sections = parseEvidenceReadingSections(value);
  if (sections.length === 0) {
    return <PitfallTextNodeContent value={value} />;
  }

  return (
    <div className="flex flex-col gap-4">
      {sections.map((section) => (
        <div key={section.title} className="min-w-0">
          <div className="ldvh-caption-strong mb-1.5 flex items-center gap-2 text-ldvh-text-secondary">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-text-secondary/45" aria-hidden="true" />
            <span>{section.title}</span>
          </div>
          <div className="ldvh-study-node-content pl-3">
            <div className="ldvh-inline-markdown max-w-none">
              <Markdown remarkPlugins={[remarkGfm]}>{section.body}</Markdown>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function parseEvidenceReadingSections(value: string): Array<{ title: string; body: string }> {
  const lines = value.split('\n');
  const sections: Array<{ title: string; body: string[] }> = [];
  let current: { title: string; body: string[] } | null = null;

  for (const line of lines) {
    const heading = line.match(/^##\s+(.+?)\s*$/);
    if (heading) {
      current = { title: heading[1].trim(), body: [] };
      sections.push(current);
      continue;
    }
    current?.body.push(line);
  }

  if (sections.length === 0) return [];
  return sections
    .sort((a, b) => {
      const aIndex = EVIDENCE_NODE_ORDER.indexOf(a.title);
      const bIndex = EVIDENCE_NODE_ORDER.indexOf(b.title);
      if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
      if (aIndex !== -1) return -1;
      if (bIndex !== -1) return 1;
      return 0;
    })
    .map((section) => ({ title: section.title, body: section.body.join('\n').trim() }))
    .filter((section) => section.body.length > 0);
}

export function RelatedContentSection({ entries, locale }: { entries: RelatedContentEntry[]; locale: string }) {
  const { t } = useI18n();
  const [state, setState] = useState<ReadingNodeState>('expanded');
  if (entries.length === 0) return null;
  return (
    <ReadingNodeSection
      title={t('objectDetail.related')}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="divide-y divide-ldvh-border/60">
        {entries.map(([fieldKey, value]) => (
          <div key={fieldKey} className="py-3 first:pt-0 last:pb-0">
            <div className="ldvh-caption-strong mb-2">{getMaterialLabel(fieldKey, locale)}</div>
            <RelatedMaterialValue fieldKey={fieldKey} value={value} locale={locale} />
          </div>
        ))}
      </div>
    </ReadingNodeSection>
  );
}

export function LoadingHint({ text }: { text: string }) {
  return (
    <div className="rounded-md border border-dashed border-ldvh-border bg-ldvh-bg/50 px-3 py-6 text-center">
      <span className="ldvh-body-muted">{text}</span>
    </div>
  );
}

export function getObjectRefType(refId: string): string | null {
  if (!isObjectRef(refId)) return null;
  return refId.match(/^([a-z]+)-\d+$/)?.[1] ?? null;
}

export function findRelatedSummary(
  refId: string,
  currentItem: RelatedObjectSummary | null,
  parentWorkCase: ObjectItem | null,
): RelatedObjectSummary | null {
  void currentItem;
  void parentWorkCase;
  void refId;
  return null;
}

export function buildCurrentFlowItem(
  obj: Record<string, unknown>,
  objType: string,
  locale: string,
  currentSummary: RelatedObjectSummary | null,
): RelatedObjectSummary {
  if (currentSummary) return currentSummary;
  const title = (locale === 'en'
    ? ((obj.title_en as string) || (obj.title as string))
    : ((obj.title_zh as string) || (obj.title as string))) || String(obj.id ?? '');
  return {
    id: String(obj.id ?? ''),
    type: objType,
    title,
    title_en: obj.title_en as string | undefined,
    title_zh: obj.title_zh as string | undefined,
    status: String(obj.status ?? 'unknown'),
    path: String(obj.path ?? ''),
    updated: String(obj.updated ?? ''),
  };
}

export function DetailObjectRow({
  label,
  item,
  fallbackId,
  objectType,
  locale,
  compact = false,
  variant = 'default',
}: {
  label: string;
  item?: RelatedObjectSummary | ObjectItem | null;
  fallbackId?: string;
  objectType: string;
  locale: string;
  compact?: boolean;
  variant?: 'default' | 'property';
}) {
  const { t } = useI18n();
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const objectId = item?.id ?? fallbackId;
  if (!objectId) return null;

  const title = item ? getLocalizedTitle(item, locale) : objectId;
  const isCurrentPanelOpen = panelOpen && panelContent?.type === 'object' && panelContent.objectType === objectType && panelContent.objectId === objectId;
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;
  const objectTypeColor = CATEGORY_COLORS[objectType] || CATEGORY_COLORS.other;
  const labelIcon = <ObjectTypeIcon type={objectType} size={12} className="shrink-0" style={{ color: objectTypeColor }} />;
  const open = () => openPanel({ type: 'object', title, objectType, objectId });
  const rowClassName = variant === 'property'
    ? 'group/detail-ref grid min-w-0 cursor-pointer items-center gap-2 py-3 text-left transition-colors first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr]'
    : `group/detail-ref grid min-w-0 cursor-pointer items-center gap-2 text-left transition-colors first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr] ${compact ? 'py-2' : 'py-3'}`;

  return (
    <div
      role="button"
      tabIndex={0}
      data-detail-object-id={objectId}
      data-detail-object-type={objectType}
      onClick={open}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          open();
        }
      }}
      className={rowClassName}
    >
      <div className={`ldvh-caption-strong text-ldvh-text-secondary ${
        variant === 'property' ? '' : 'flex min-w-0 items-center gap-1.5'
      }`}
      >
        {variant !== 'property' && labelIcon}
        <span className="min-w-0 truncate">{label}</span>
      </div>
      <div className={`flex min-w-0 items-center gap-2 transition-colors ${
        variant === 'property'
          ? 'ldvh-definition-text'
          : 'rounded-md px-2 py-1.5 group-hover/detail-ref:bg-ldvh-border/35'
      }`}
      >
        {variant === 'property' && labelIcon}
        <span className="ldvh-body min-w-0 flex-1 truncate transition-colors group-hover/detail-ref:text-ldvh-accent">{title}</span>
        {variant !== 'property' && <span className="ldvh-meta-muted shrink-0">{objectId}</span>}
        {variant !== 'property' && item?.status && <StatusBadge status={item.status} statusLabel={getObjectStatusLocale(objectType, item.status, locale)} objectType={objectType} size="sm" />}
        <CopyPathButton path={item?.path} label={t('common.copyObjectPath')} copiedLabel={t('common.copiedObjectPath')} />
        <PanelIcon size={16} className={`shrink-0 transition-colors ${isCurrentPanelOpen ? 'text-ldvh-accent' : 'text-ldvh-text-secondary group-hover/detail-ref:text-ldvh-accent'}`} />
      </div>
    </div>
  );
}

export function getAuxiliaryMetaEntries(obj: Record<string, unknown>, objType: string) {
  const keys = Array.from(new Set([...(AUXILIARY_META_KEYS_BY_TYPE[objType] || []), ...COMMON_AUXILIARY_META_KEYS]));
  return keys
    .filter((key) => key !== 'priority' || (objType !== 'spark' && objType !== 'workcase'))
    .map((key) => [key, obj[key]] as [string, unknown])
    .filter(([, value]) => value !== null && value !== undefined && value !== '' && (!Array.isArray(value) || value.length > 0));
}

export function getFieldLabel(fieldKey: string, locale: string) {
  const labelEntry = FIELD_LABEL_LOCALES[fieldKey];
  return labelEntry ? (locale === 'en' ? labelEntry.en : labelEntry.zh) : fieldKey.replace(/_/g, ' ');
}

function localizeMetaValue(fieldKey: string, rawValue: string, locale: string) {
  if (fieldKey === 'tags') return rawValue.trim();
  if (isSignalField(fieldKey)) {
    return getSignalText(fieldKey, rawValue, locale) || rawValue.trim();
  }
  const normalized = rawValue.trim();
  const entry = FIELD_VALUE_LOCALES[fieldKey]?.[normalized];
  if (entry) return locale === 'en' ? entry.en : entry.zh;
  return normalized.replace(/_/g, ' ');
}

function MetaValueChip({ fieldKey, value, children }: { fieldKey?: string; value?: unknown; children: ReactNode }) {
  const signalClass = fieldKey && isSignalField(fieldKey)
    ? getSignalClassName(fieldKey, value)
    : 'border-ldvh-border bg-ldvh-bg text-ldvh-text-primary';
  return (
    <span className={`ldvh-chip rounded-md border px-2 py-0.5 font-sans ${signalClass}`}>
      {children}
    </span>
  );
}

function formatAuxiliaryMetaValue(fieldKey: string, value: unknown, locale: string): ReactNode {
  if (fieldKey === 'source') return localizeMetaValue(fieldKey, String(value), locale);

  if (Array.isArray(value)) {
    return (
      <span className="flex flex-wrap gap-1.5">
        {value.map((item, index) => (
          <MetaValueChip key={`${fieldKey}-${index}`} fieldKey={fieldKey} value={item}>
            {localizeMetaValue(fieldKey, String(item), locale)}
          </MetaValueChip>
        ))}
      </span>
    );
  }

  return (
    <MetaValueChip fieldKey={fieldKey} value={value}>
      {localizeMetaValue(fieldKey, String(value), locale)}
    </MetaValueChip>
  );
}

export function DetailSection({
  title,
  tone,
  icon,
  children,
}: {
  title: string;
  tone: 'primary' | 'checklist' | 'evidence' | 'docs' | 'default';
  icon?: ReactNode;
  children: ReactNode;
}) {
  const { locale } = useI18n();
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const StateIcon = getReadingNodeIcon(state);
  const toneClass = {
    primary: 'border-ldvh-border bg-ldvh-panel',
    checklist: 'border-ldvh-border bg-ldvh-panel',
    evidence: 'border-ldvh-border bg-ldvh-panel',
    docs: 'border-ldvh-border bg-ldvh-panel',
    default: 'border-ldvh-border bg-ldvh-panel',
  }[tone];

  return (
    <section className={`rounded-xl border p-4 ${toneClass}`}>
      <button
        type="button"
        onClick={() => setState((current) => getReadingNodeNextState(current))}
        aria-label={getReadingNodeAriaLabel(title, state, locale)}
        className={`ldvh-section-title flex w-full min-w-0 items-center gap-2 text-left transition-colors hover:text-ldvh-accent ${state === 'collapsed' ? '' : 'mb-3'}`}
      >
        {icon ?? <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-accent" />}
        <span className="min-w-0 flex-1 truncate">{title}</span>
        <StateIcon size={14} className="shrink-0 text-ldvh-text-secondary/80" aria-hidden="true" />
      </button>
      {state !== 'collapsed' && children}
    </section>
  );
}

function getReadingNodeNextState(state: ReadingNodeState): ReadingNodeState {
  return state === 'collapsed' ? 'expanded' : 'collapsed';
}

function getReadingNodeIcon(state: ReadingNodeState) {
  if (state === 'collapsed') return ChevronDown;
  return ChevronUp;
}

function getReadingNodeAriaLabel(title: string, state: ReadingNodeState, locale: string) {
  const nextState = getReadingNodeNextState(state);
  if (locale === 'en') {
    const action = nextState === 'collapsed' ? 'Collapse' : 'Expand';
    return `${action} ${title}`;
  }
  const action = nextState === 'collapsed' ? '收拢' : '展开';
  return `${action}${title}`;
}

function ReadingNodeSection({
  title,
  state,
  locale,
  children,
  onToggle,
}: {
  title: string;
  state: ReadingNodeState;
  locale: string;
  children: ReactNode;
  onToggle: () => void;
}) {
  const StateIcon = getReadingNodeIcon(state);

  return (
    <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
      <button
        type="button"
        onClick={onToggle}
        aria-label={getReadingNodeAriaLabel(title, state, locale)}
        className={`ldvh-section-title flex w-full min-w-0 items-center gap-2 text-left transition-colors hover:text-ldvh-accent ${state === 'collapsed' ? '' : 'mb-3'}`}
      >
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-accent" />
        <span className="min-w-0 flex-1 truncate">{title}</span>
        <StateIcon size={14} className="shrink-0 text-ldvh-text-secondary/80" aria-hidden="true" />
      </button>
      {state !== 'collapsed' && children}
    </section>
  );
}

export function DetailInlineField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid gap-2 py-3 first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr]">
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{label}</div>
      <div className="min-w-0">{value}</div>
    </div>
  );
}

export function DetailDocGroup({ label, docs }: { label: string; docs?: string[] }) {
  if (!docs || docs.length === 0) return null;
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-bg/40 p-3">
      <div className="ldvh-caption-strong mb-2">{label}</div>
      <DocPreviewLink docs={docs} />
    </div>
  );
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

function DocumentOrTextList({ items, fieldKey, variant = 'card' }: { items: string[]; fieldKey: string; variant?: 'card' | 'plain' }) {
  const docs = items.filter((item) => isPreviewablePathForField(fieldKey, item));
  const rest = items.filter((item) => !isPreviewablePathForField(fieldKey, item));
  return (
    <div className="flex flex-col gap-2">
      {docs.length > 0 && <DocPreviewLink docs={docs} variant={variant} />}
      {rest.length > 0 && <StringList items={rest} />}
    </div>
  );
}

export function EmptyHint({ text }: { text: string }) {
  return <span className="ldvh-body-muted">{text}</span>;
}

/** 内容字段：根据字段类型选择渲染方式和样式 */
function basename(path: string) {
  return path.split('/').filter(Boolean).pop() || path;
}

const STUDY_READING_NODES: Array<{ field: string; zh: string; en: string; kind: 'text' | 'report' }> = [
  { field: 'user_intent', zh: '意图', en: 'Intent', kind: 'text' },
  { field: 'summary', zh: '摘要', en: 'Summary', kind: 'text' },
  { field: 'conclusion', zh: '建议', en: 'Recommendation', kind: 'text' },
  { field: 'report_body', zh: '正文', en: 'Report body', kind: 'report' },
];

function isDetailRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function detailString(value: unknown, fallback = ''): string {
  if (value === null || value === undefined) return fallback;
  if (value instanceof Date) return value.toISOString();
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return String(value);
}

function detailStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => detailString(item).trim())
    .filter((item) => item.length > 0);
}

function getWorkCaseOrchestration(obj: Record<string, unknown>): Record<string, unknown> {
  return isDetailRecord(obj.orchestration) ? obj.orchestration : {};
}

function getWorkCaseExecutionItems(obj: Record<string, unknown>): RelatedObjectSummary[] {
  const orchestration = getWorkCaseOrchestration(obj);
  const rawItems = Array.isArray(orchestration.execution_items) ? orchestration.execution_items : [];
  return rawItems
    .map((rawItem, index): RelatedObjectSummary | null => {
      if (!isDetailRecord(rawItem)) return null;
      const id = detailString(rawItem.id, `execution-item-${index + 1}`);
      return {
        id,
        type: 'execution_item',
        title: detailString(rawItem.title, id),
        status: detailString(rawItem.status, 'unknown'),
        path: detailString(obj.path),
        updated: detailString(obj.updated),
        role: detailString(rawItem.role) || undefined,
        mode: detailString(rawItem.mode) || undefined,
        expectedOutput: detailString(rawItem.expected_output) || undefined,
        resultSummary: detailString(rawItem.result_summary) || undefined,
        blockingReason: detailString(rawItem.blocking_reason) || undefined,
        inputRefs: detailStringArray(rawItem.input_refs),
        evidenceRefs: detailStringArray(rawItem.evidence_refs),
      } satisfies RelatedObjectSummary;
    })
    .filter((item): item is RelatedObjectSummary => Boolean(item));
}

export function StudyReadingLayout({
  obj,
  extraEntries,
  relatedEntries,
  locale,
  objectPath,
}: {
  obj: Record<string, unknown>;
  extraEntries: Array<[string, unknown]>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
  objectPath?: string;
}) {
  const extraPrimaryEntries = extraEntries.filter(([fieldKey]) => !STUDY_READING_NODE_FIELDS.has(fieldKey));

  return (
    <div className="mb-6 flex flex-col gap-5">
      {STUDY_READING_NODES.map((node) => (
        <StudyReadingNode
          key={node.field}
          title={locale === 'en' ? node.en : node.zh}
          value={obj[node.field]}
          locale={locale}
          kind={node.kind}
          objectPath={objectPath}
        />
      ))}
      {extraPrimaryEntries.map(([fieldKey, value]) => (
        <ContentField
          key={fieldKey}
          fieldKey={fieldKey}
          value={value}
          locale={locale}
          objType="study"
          objectPath={objectPath}
        />
      ))}
      <RelatedContentSection entries={relatedEntries} locale={locale} />
    </div>
  );
}

function StudyReadingNode({
  title,
  value,
  locale,
  kind,
  objectPath,
}: {
  title: string;
  value: unknown;
  locale: string;
  kind: 'text' | 'report';
  objectPath?: string;
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  if (!hasDetailContent(value)) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      {kind === 'report' ? (
        <StudyReportBodyEntry value={value} objectPath={objectPath} locale={locale} />
      ) : (
        <StudyTextNodeContent value={value} />
      )}
    </ReadingNodeSection>
  );
}

function StudyReportBodyEntry({ value, objectPath, locale }: { value: unknown; objectPath?: string; locale: string }) {
  const { t } = useI18n();
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const docPath = objectPath || 'study-report.md';
  const title = objectPath ? basename(objectPath) : (locale === 'en' ? 'Report body' : '报告正文');
  const openLabel = locale === 'en' ? 'Open in reading panel' : '扩展阅读';
  const isCurrentPanelOpen = Boolean(panelOpen && panelContent?.type === 'doc' && panelContent.docPath === docPath);
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;

  const openReportBody = () => {
    openPanel({ type: 'doc', title, docPath, data: String(value) });
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    openReportBody();
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={openReportBody}
      onKeyDown={handleKeyDown}
      title={openLabel}
      className="ldvh-body group flex w-full cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50"
    >
      <BookOpenText size={13} className="shrink-0 text-ldvh-accent" />
      <span className="ldvh-meta-primary min-w-0 flex-1 truncate">{title}</span>
      <CopyPathButton path={objectPath} label={t('common.copyDocPath')} copiedLabel={t('common.copiedDocPath')} />
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          openReportBody();
        }}
        title={openLabel}
        aria-label={openLabel}
        className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-transparent bg-transparent text-ldvh-text-secondary/70 transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-accent focus-visible:border-ldvh-accent/50 focus-visible:outline-none"
      >
        <PanelIcon size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

function StudyTextNodeContent({ value, compact = false }: { value: unknown; compact?: boolean }) {
  const text = String(value);

  return (
    <div className={`ldvh-study-node-content min-w-0 ${compact ? 'ldvh-study-node-content-compact' : ''}`}>
      <div className="ldvh-inline-markdown max-w-none min-w-0 overflow-hidden break-words">
        <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown>
      </div>
    </div>
  );
}

export function ContentField({ fieldKey, value, locale }: { fieldKey: string; value: unknown; locale: string; objType?: string; objectPath?: string }) {
  const isCollapsible = COLLAPSIBLE_FIELDS.includes(fieldKey);
  const [collapsed, setCollapsed] = useState(Boolean(isCollapsible));

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
        <h4 className="ldvh-caption-strong">{label}</h4>
        {isCollapsible && (
          <span className="ml-auto text-ldvh-text-secondary">
            {collapsed ? <ChevronRight size={13} /> : <ChevronDown size={13} />}
          </span>
        )}
      </div>
      {!collapsed && <FieldValue fieldKey={fieldKey} value={value} depth={0} locale={locale} />}
    </div>
  );
}

function FieldValue({ fieldKey, value, depth, locale }: { fieldKey: string; value: unknown; depth: number; locale: string }) {
  const { t } = useI18n();
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

    if (CHECKLIST_COMPAT_FIELDS.includes(fieldKey) && hasChecklist(value)) {
      return <ChecklistCard value={value} />;
    }

    if (DOC_LINK_FIELDS.includes(fieldKey) && isPreviewablePathForField(fieldKey, value)) {
      return <DocPreviewLink docs={[value]} />;
    }

    if (PATH_TEXT_FIELDS.includes(fieldKey)) {
      return <PathText value={value} />;
    }

    if (EVIDENCE_FIELDS.includes(fieldKey)) {
      return <EvidenceBlock value={value} embedded />;
    }

    // 长文本字段使用 SummaryText 组件
    if (SUMMARY_TEXT_FIELDS.includes(fieldKey)) {
      return <SummaryText value={value} />;
    }

    // 单字符串引用字段使用 ReferenceCard
    if (REFERENCE_FIELDS.includes(fieldKey) && parseRefType(value)) {
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
        return <DocumentOrTextList items={value as string[]} fieldKey={fieldKey} />;
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
              <span className="ldvh-caption shrink-0 rounded border border-ldvh-border bg-ldvh-bg px-1.5 py-0.5">
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

  return <span className="ldvh-body">{String(value)}</span>;
}

/** 从引用 ID 解析对象类型（如 workcase-0001 → workcase） */
function parseRefType(refId: string): string | null {
  if (!isObjectRef(refId)) return null;
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
