import { useEffect, useState, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowLeft, ChevronDown, ChevronRight, ChevronUp, Code2, FileText, Info, PanelRightClose, PanelRightOpen } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import StatusBadge from '@/components/StatusBadge';
import ChecklistCard from '@/components/ChecklistCard';
import ReferenceCard from '@/components/ReferenceCard';
import SummaryText from '@/components/SummaryText';
import DocPreviewLink from '@/components/DocPreviewLink';
import EvidenceBlock from '@/components/EvidenceBlock';
import CopyPathButton from '@/components/CopyPathButton';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { TaskFlowBar, TaskFlowMarker } from '@/components/TaskFlowStatus';
import { getTaskFlowLabel, getTaskFlowTone, sortPlanTasks, taskFlowDetailActionClass, taskFlowDetailHoverTextClass, taskFlowRowClass } from '@/utils/taskFlowStatus';
import { fetchObjectDetail, fetchObjects, type ObjectDetail, type ObjectItem, type RelatedObjectSummary, type RelatedPlanSummary } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import { getObjectStatusHint, getObjectStatusLocale, getTypeDescription } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { formatDateTime } from '@/utils/dateFormat';
import { getSignalClassName, getSignalText, isSignalField } from '@/utils/objectSignals';
import { usePanel } from '@/utils/panelContext';
import {
  CHECKLIST_COMPAT_FIELDS,
  COLLAPSIBLE_FIELDS,
  DOC_LINK_FIELDS,
  EVIDENCE_FIELDS,
  PATH_TEXT_FIELDS,
  REFERENCE_FIELDS,
  SUMMARY_TEXT_FIELDS,
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
  'aggregated_deliverables',
  'aggregated_docs',
  'aggregated_related_docs',
  'aggregated_related_adrs',
  'aggregated_related_memos',
  'aggregated_related_pitfalls',
  'aggregated_related_changes',
];
const TASK_AUXILIARY_META_KEYS = ['assignee'];
const COMMON_AUXILIARY_META_KEYS = ['priority', 'importance', 'repeatability', 'tags', 'scope', 'impact', 'assignee'];
const AUXILIARY_META_KEYS_BY_TYPE: Record<string, string[]> = {
  task: TASK_AUXILIARY_META_KEYS,
  memo: ['priority', 'tags'],
  profile: ['project_name', 'project_kind', 'language', 'framework'],
  pitfall: ['repeatability', 'tags'],
};
/** Task 类型字段展示优先顺序 */
export const TASK_FIELD_ORDER = [
  'description',
  'source',
  'acceptance',
  'blocked_by',
  'verification',
  'closure_evidence',
  'deliverables',
  'related_docs',
  'affected_docs',
  'related_adrs',
  'related_changes',
];
const FIELD_ORDER_BY_TYPE: Record<string, string[]> = {
  workarea: ['description', 'source', 'scope', 'constraints', 'related_docs', 'related_adrs', 'related_memos', 'related_pitfalls'],
  taskplan: ['workarea', 'description', 'success_criteria', 'source', 'tasks', 'completion_evidence', 'related_docs'],
  task: TASK_FIELD_ORDER,
  subtask: ['task', 'description', 'source', 'acceptance', 'blocked_by', 'verification', 'closure_evidence'],
  profile: [
    'description', 'project_path', 'ldvh_base_path', 'docs_path',
    'governance_scope', 'related_workareas', 'related_taskplans', 'related_tasks', 'related_adrs',
    'related_memos', 'related_pitfalls', 'related_docs', 'related_changes',
    'status_history', 'notes',
  ],
  pitfall: [
    'symptoms', 'trigger_conditions', 'root_cause', 'resolution', 'verification',
    'avoidance', 'applicability', 'source_tasks', 'source_memos', 'related_workareas', 'related_taskplans',
    'related_adrs', 'related_profiles', 'related_docs', 'related_rules',
    'related_changes', 'superseded_by', 'archive_reason', 'discard_reason', 'status_history', 'notes',
  ],
};

const DETAIL_TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'discarded', 'superseded']);
const DETAIL_PENDING_CLOSE_STATUSES = new Set(['review_needed']);
const WORK_OBJECT_DETAIL_TYPES = new Set(['workarea', 'taskplan', 'task', 'subtask']);

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
  workarea: { zh: '工作域', en: 'Work Area' },
  taskplan: { zh: '任务计划', en: 'Task Plan' },
  task: { zh: '任务', en: 'Task' },
  subtask: { zh: '子任务', en: 'Subtask' },
  adr: { zh: '决策', en: 'ADR' },
  pitfall: { zh: '踩坑经验', en: 'Pitfall' },
  memo: { zh: '备忘', en: 'Memo' },
  profile: { zh: '画像', en: 'Profile' },
  change: { zh: '变更', en: 'Change' },
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
  description: { zh: '描述', en: 'Description' },
  summary: { zh: '摘要', en: 'Summary' },
  details: { zh: '详情', en: 'Details' },
  background: { zh: '背景', en: 'Background' },
  motivation: { zh: '动机', en: 'Motivation' },
  outcome: { zh: '结果', en: 'Outcome' },
  next_steps: { zh: '后续步骤', en: 'Next Steps' },
  lessons: { zh: '经验教训', en: 'Lessons' },
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
  workarea: { zh: '工作域', en: 'Work Area' },
  taskplan: { zh: '任务计划', en: 'Task Plan' },
  task: { zh: '所属任务', en: 'Task' },
  tasks: { zh: '任务', en: 'Tasks' },
  blocked_by: { zh: '前置依赖', en: 'Blocked By' },
  closure_evidence: { zh: '关闭证据', en: 'Closure Evidence' },
  completion_evidence: { zh: '完成证据', en: 'Completion Evidence' },
  review_requested_at: { zh: '请求关闭确认时间', en: 'Review Requested At' },
  transition_reasons: { zh: '流转记录', en: 'Transition Reasons' },
  options: { zh: '选项', en: 'Options' },
  decision: { zh: '决策', en: 'Decision' },
  alternatives: { zh: '替代方案', en: 'Alternatives' },
  related_tasks: { zh: '关联任务', en: 'Related Tasks' },
  related_subtasks: { zh: '关联子任务', en: 'Related Subtasks' },
  related_workareas: { zh: '关联工作域', en: 'Related Work Areas' },
  related_taskplans: { zh: '关联任务计划', en: 'Related Task Plans' },
  related_adrs: { zh: '关联决策', en: 'Related ADRs' },
  related_memos: { zh: '关联备忘', en: 'Related Memos' },
  related_pitfalls: { zh: '关联踩坑经验', en: 'Related Pitfalls' },
  related_profiles: { zh: '关联画像', en: 'Related Profiles' },
  source_objects: { zh: '来源对象', en: 'Source Objects' },
  related_objects: { zh: '关联对象', en: 'Related Objects' },
  source_tasks: { zh: '来源任务', en: 'Source Tasks' },
  source_memos: { zh: '来源备忘', en: 'Source Memos' },
  resolved_to: { zh: '分流目标', en: 'Resolved To' },
  resolved_at: { zh: '分流时间', en: 'Resolved At' },
  discard_reason: { zh: '废弃原因', en: 'Discard Reason' },
  superseded_by: { zh: '替代来源', en: 'Superseded By' },
  related_changes: { zh: '关联变更', en: 'Related Changes' },
  affects: { zh: '影响对象', en: 'Affects' },
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
  repeatability: { zh: '复现概率', en: 'Repeatability' },
  related_rules: { zh: '承接规则', en: 'Related Rules' },
  status_history: { zh: '状态记录', en: 'Status History' },
  changes: { zh: '变更列表', en: 'Changes' },
  related_docs: { zh: '关联文档', en: 'Related Docs' },
  affected_docs: { zh: '影响文档', en: 'Affected Docs' },
  deliverables: { zh: '产出物', en: 'Deliverables' },
  aggregated_deliverables: { zh: '聚合产出物', en: 'Aggregated Deliverables' },
  aggregated_docs: { zh: '聚合文档', en: 'Aggregated Docs' },
  aggregated_related_docs: { zh: '聚合关联文档', en: 'Aggregated Related Docs' },
  aggregated_related_adrs: { zh: '聚合关联决策', en: 'Aggregated Related ADRs' },
  aggregated_related_memos: { zh: '聚合关联备忘', en: 'Aggregated Related Memos' },
  aggregated_related_pitfalls: { zh: '聚合关联踩坑经验', en: 'Aggregated Related Pitfalls' },
  aggregated_related_changes: { zh: '聚合关联变更', en: 'Aggregated Related Changes' },
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
  repeatability: {
    recurring: { zh: '反复出现', en: 'Recurring' },
    occasional: { zh: '偶发', en: 'Occasional' },
    one_off: { zh: '一次性', en: 'One-off' },
  },
  tags: {
    'ai-collaboration': { zh: 'AI 协作', en: 'AI Collaboration' },
    'border-radius': { zh: '圆角', en: 'Border Radius' },
    consistency: { zh: '一致性', en: 'Consistency' },
    'fact-model': { zh: '事实模型', en: 'Fact Model' },
    'frontend-gotcha': { zh: '前端问题', en: 'Frontend Gotcha' },
    'process-improvement': { zh: '流程改进', en: 'Process Improvement' },
    rules: { zh: '规则', en: 'Rules' },
    'single-authority': { zh: '单一权威源', en: 'Single Authority' },
    'spec-tools-sync': { zh: '规范工具同步', en: 'Spec/Tools Sync' },
    specs: { zh: '规范', en: 'Specs' },
    subdocument: { zh: '子文档', en: 'Subdocument' },
    'tailwind-css': { zh: 'Tailwind CSS', en: 'Tailwind CSS' },
    'task-lifecycle': { zh: '任务生命周期', en: 'Task Lifecycle' },
    'transition-animation': { zh: '过渡动画', en: 'Transition Animation' },
    verification: { zh: '验证', en: 'Verification' },
    yaml: { zh: 'YAML', en: 'YAML' },
  },
};

export default function ObjectDetail() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [workareaSummary, setWorkareaSummary] = useState<ObjectItem | null>(null);
  const [workareaSummaryLoading, setWorkareaSummaryLoading] = useState(false);
  const [relatedPlanSummary, setRelatedPlanSummary] = useState<ObjectItem | null>(null);
  const [relatedTaskSummary, setRelatedTaskSummary] = useState<RelatedObjectSummary | null>(null);
  const [relatedSummaryLoading, setRelatedSummaryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showYaml, setShowYaml] = useState(false);
  const { t, getStatus, locale } = useI18n();



  useEffect(() => {
    if (!type || !id) return;
    let cancelled = false;
    setDetail(null);
    setWorkareaSummary(null);
    setRelatedPlanSummary(null);
    setRelatedTaskSummary(null);
    setWorkareaSummaryLoading(type === 'workarea');
    setRelatedSummaryLoading(type === 'taskplan' || type === 'task' || type === 'subtask');
    setError(null);

    fetchObjectDetail(type, id)
      .then((result) => {
        if (!cancelled) setDetail(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    if (type === 'workarea') {
      fetchObjects('workarea')
        .then((result) => {
          if (cancelled) return;
          setWorkareaSummary(result.data?.items?.find((item) => item.id === id) ?? null);
        })
        .catch(() => {
          if (!cancelled) setWorkareaSummary(null);
        })
        .finally(() => {
          if (!cancelled) setWorkareaSummaryLoading(false);
        });
    }

    if (type === 'taskplan' || type === 'task' || type === 'subtask') {
      fetchObjects('taskplan')
        .then((result) => {
          if (cancelled) return;
          const plans = result.data?.items ?? [];
          if (type === 'taskplan') {
            setRelatedPlanSummary(plans.find((plan) => plan.id === id) ?? null);
            return;
          }

          const plan = plans.find((candidate) => candidate.tasks?.some((task) => {
            if (type === 'task') return task.id === id;
            return task.subtasks?.some((subtask) => subtask.id === id);
          })) ?? null;
          const task = plan?.tasks?.find((candidate) => {
            if (type === 'task') return candidate.id === id;
            return candidate.subtasks?.some((subtask) => subtask.id === id);
          }) ?? null;
          setRelatedPlanSummary(plan);
          setRelatedTaskSummary(task);
        })
        .catch(() => {
          if (!cancelled) {
            setRelatedPlanSummary(null);
            setRelatedTaskSummary(null);
          }
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
  const typeDesc = getTypeDescription(objType, locale);
  const statusHint = objType === 'workarea' ? '' : getObjectStatusHint(objType, objStatus, locale);
  const isWorkObject = WORK_OBJECT_DETAIL_TYPES.has(objType);

  const displayTitle = (locale === 'en'
    ? ((obj.title_en as string) || obj.title as string)
    : ((obj.title_zh as string) || obj.title as string)) || objId;

  const contentEntries = getObjectDetailContentEntries(obj, objType);

  const auxiliaryMetaEntries = objType === 'workarea' ? [] : getAuxiliaryMetaEntries(obj, objType);

  // 生成真正的 YAML 源码
  const yamlSource = objectToYaml(obj);
  const listSearch = searchParams.toString();
  const listPath = `/objects/${objType}${listSearch ? `?${listSearch}` : ''}`;
  const currentPath = `${location.pathname}${location.search}`;
  const returnPath = getReturnPath(location.state, currentPath) ?? listPath;

  return (
    <div className="flex h-full">
      {/* Main content area */}
      <div className="flex-1 overflow-y-auto rounded-none transition-[margin] duration-300">
        <div className="mx-auto max-w-4xl p-4 sm:p-6">
          <div className="sticky top-0 z-20 -mx-4 mb-6 border-b border-ldvh-border bg-ldvh-bg/95 px-4 pb-4 pt-4 backdrop-blur sm:-mx-6 sm:px-6">
          {/* Header */}
          <div>
            <button
              onClick={() => navigate(returnPath)}
              className="ldvh-body-muted mb-3 flex items-center gap-1.5 rounded-md px-2 py-1 transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
            >
              <ArrowLeft size={14} />
              {t('objectDetail.back')}
            </button>
            {isWorkObject ? (
              <WorkObjectDetailHeader
                title={displayTitle}
                id={objId}
                target={detail.target}
                objectType={objType}
                typeColor={typeColor}
                typeLabel={TYPE_LOCALES[objType] ? (locale === 'en' ? TYPE_LOCALES[objType].en : TYPE_LOCALES[objType].zh) : objType}
                source={obj}
                locale={locale}
                created={formatDateTime(obj.created as string | undefined)}
                updated={formatDateTime(obj.updated as string | undefined)}
              />
            ) : (
              <>
                <div className="flex items-start gap-3">
                  <span
                    className="ldvh-chip mt-1 shrink-0 rounded px-2 py-0.5"
                    style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
                  >
                    {TYPE_LOCALES[objType] ? (locale === 'en' ? TYPE_LOCALES[objType].en : TYPE_LOCALES[objType].zh) : objType}
                  </span>
                  <div className="min-w-0 flex-1">
                    <h1 className="ldvh-page-title flex min-w-0 items-center gap-2">
                      <PriorityIcon source={obj} type={objType} locale={locale} size="lg" />
                      <ObjectTypeIcon type={objType} size={18} className="shrink-0" style={{ color: typeColor }} />
                      <span className="min-w-0 truncate">{displayTitle}</span>
                    </h1>
                    <p className="ldvh-meta mt-0.5">{objId}</p>
                    {typeDesc && (
                      <p className="ldvh-caption mt-1">{typeDesc}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1.5">
                    <div className="flex items-center gap-2">
                      <CopyPathButton path={detail.target} />
                      <StatusBadge status={objStatus} statusLabel={getObjectStatusLocale(objType, objStatus, locale)} size="md" />
                    </div>
                    {statusHint && (
                      <span className="ldvh-caption">{statusHint}</span>
                    )}
                  </div>
                </div>
                {objType === 'taskplan' && objStatus === 'review_needed' && (
                  <div className="mt-3 flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                    <Info size={14} className="shrink-0 text-amber-400" />
                    <span className="ldvh-caption text-amber-300">{t('objectDetail.humanGateTip')}</span>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Metadata row */}
          {!isWorkObject && (
            <div className="mt-4 flex flex-wrap gap-2">
              <MetaChip label={t('objectDetail.created')} value={formatDateTime(obj.created as string | undefined)} />
              <MetaChip label={t('objectDetail.updated')} value={formatDateTime(obj.updated as string | undefined)} />
              {obj.closed_at && <MetaChip label={t('objectDetail.closedAt')} value={formatDateTime(obj.closed_at as string)} />}
              {auxiliaryMetaEntries.map(([key, value]) => (
                <MetaChip key={key} label={getFieldLabel(key, locale)} value={formatAuxiliaryMetaValue(key, value, locale)} />
              ))}
            </div>
          )}
          </div>

          {/* Content fields */}
          {objType === 'workarea' ? (
            <WorkAreaReadingLayout
              obj={obj}
              summary={workareaSummary}
              loading={workareaSummaryLoading}
              locale={locale}
              getStatus={getStatus}
            />
          ) : objType === 'taskplan' ? (
            <TaskPlanReadingLayout
              obj={obj}
              summary={relatedPlanSummary}
              loading={relatedSummaryLoading}
              locale={locale}
              getStatus={getStatus}
            />
          ) : objType === 'task' || objType === 'subtask' ? (
            <TaskReadingLayout
              obj={obj}
              locale={locale}
              objType={objType}
              summary={relatedTaskSummary}
              parentPlan={relatedPlanSummary}
              loading={relatedSummaryLoading}
              getStatus={getStatus}
            />
          ) : (
            <div className="mb-6 flex flex-col gap-5">
              {contentEntries.map(([key, value]) => (
                <ContentField key={key} fieldKey={key} value={value} locale={locale} objType={objType} />
              ))}
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

function WorkObjectDetailHeader({
  title,
  id,
  target,
  objectType,
  typeColor,
  typeLabel,
  source,
  locale,
  created,
  updated,
}: {
  title: string;
  id: string;
  target?: string;
  objectType: string;
  typeColor: string;
  typeLabel: string;
  source: Record<string, unknown>;
  locale: string;
  created: string;
  updated: string;
}) {
  const { t } = useI18n();
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel px-4 py-3">
      <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="mb-1.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
            <span
              className="ldvh-chip shrink-0 rounded px-2 py-0.5"
              style={{ backgroundColor: `${typeColor}18`, color: typeColor }}
            >
              {typeLabel}
            </span>
            <ObjectSignalBadges source={source} type={objectType} locale={locale} />
            <span className="ldvh-meta-muted min-w-0 truncate">{id}</span>
          </div>
          <h1 className="ldvh-page-title flex min-w-0 items-center gap-2 break-words">
            <PriorityIcon source={source} type={objectType} locale={locale} size="lg" />
            <ObjectTypeIcon type={objectType} size={18} className="shrink-0" style={{ color: typeColor }} />
            <span className="min-w-0">{title}</span>
          </h1>
          <div className="mt-2 flex min-w-0 flex-wrap items-center gap-x-4 gap-y-1">
            <HeaderDateMeta label={t('objectDetail.createdShort')} value={created} />
            <HeaderDateMeta label={t('objectDetail.updatedShort')} value={updated} />
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 sm:pt-0.5">
          <CopyPathButton path={target} />
        </div>
      </div>
    </div>
  );
}

function HeaderDateMeta({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-1.5">
      <span className="ldvh-caption shrink-0">{label}</span>
      <span className="ldvh-meta-muted min-w-0 truncate text-ldvh-text-secondary">{value}</span>
    </span>
  );
}

function isDetailTerminalStatus(status: string): boolean {
  return DETAIL_TERMINAL_STATUSES.has(status);
}

function isDetailPendingCloseStatus(status: string): boolean {
  return DETAIL_PENDING_CLOSE_STATUSES.has(status);
}

export function WorkAreaReadingLayout({
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
  const { openPanel } = usePanel();
  const plans = summary?.plans ?? [];
  const activePlans = plans.filter((plan) => !isDetailPendingCloseStatus(plan.status) && !isDetailTerminalStatus(plan.status));
  const pendingClosePlans = plans.filter((plan) => isDetailPendingCloseStatus(plan.status));
  const closedPlans = plans.filter((plan) => isDetailTerminalStatus(plan.status));
  const hasRelatedMaterials = [
    obj.related_docs,
    obj.related_adrs,
    obj.related_memos,
    obj.related_pitfalls,
  ].some((value) => Array.isArray(value) && value.length > 0);

  const openPlan = (plan: RelatedPlanSummary) => {
    openPanel({
      type: 'object',
      title: getLocalizedTitle(plan, locale),
      objectType: 'taskplan',
      objectId: plan.id,
    });
  };

  return (
    <div className="mb-6 flex flex-col gap-5">
      {loading ? (
        <div className="rounded-xl border border-dashed border-ldvh-border bg-ldvh-panel px-3 py-6 text-center">
          <span className="ldvh-body-muted">{t('objectDetail.workareaPlansLoading')}</span>
        </div>
      ) : plans.length === 0 ? (
        <div className="rounded-xl border border-dashed border-ldvh-border bg-ldvh-panel px-3 py-6 text-center">
          <span className="ldvh-body-muted">{t('objectList.noPlans')}</span>
        </div>
      ) : (
        <>
          {activePlans.length > 0 && (
            <WorkAreaPlanGroup
              title={t('objectList.activePlanCount', { count: String(activePlans.length) })}
              tone="active"
              plans={activePlans}
              locale={locale}
              getStatus={getStatus}
              onOpen={openPlan}
            />
          )}
          {pendingClosePlans.length > 0 && (
            <WorkAreaPlanGroup
              title={t('objectList.pendingClosePlanCount', { count: String(pendingClosePlans.length) })}
              tone="review"
              plans={pendingClosePlans}
              locale={locale}
              getStatus={getStatus}
              onOpen={openPlan}
            />
          )}
          {closedPlans.length > 0 && (
            <WorkAreaPlanGroup
              title={t('objectList.closedPlanCount', { count: String(summary?.planClosed ?? closedPlans.length) })}
              tone="closed"
              plans={closedPlans}
              locale={locale}
              getStatus={getStatus}
              onOpen={openPlan}
              defaultCollapsed
            />
          )}
        </>
      )}

      <WorkAreaDefinitionSection title={t('objectDetail.workareaGoal')} value={obj.description} />
      <WorkAreaDefinitionSection title={getFieldLabel('scope', locale)} value={obj.scope} />
      <WorkAreaDefinitionSection title={getFieldLabel('constraints', locale)} value={obj.constraints} />
      <WorkAreaDefinitionSection title={getFieldLabel('source', locale)} value={obj.source} muted />

      {hasRelatedMaterials && (
        <>
          <WorkAreaMaterialSection fieldKey="related_docs" value={obj.related_docs} locale={locale} />
          <WorkAreaMaterialSection fieldKey="related_adrs" value={obj.related_adrs} locale={locale} />
          <WorkAreaMaterialSection fieldKey="related_memos" value={obj.related_memos} locale={locale} />
          <WorkAreaMaterialSection fieldKey="related_pitfalls" value={obj.related_pitfalls} locale={locale} />
        </>
      )}
    </div>
  );
}

function WorkAreaSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
      <h2 className="ldvh-section-title mb-3 flex min-w-0 items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-ldvh-accent" />
        <span className="min-w-0 truncate">{title}</span>
      </h2>
      {children}
    </section>
  );
}

function WorkAreaDefinitionSection({ title, value, muted = false }: { title: string; value: unknown; muted?: boolean }) {
  if (!hasDetailContent(value)) return null;
  return (
    <WorkAreaSection title={title}>
      <div className={`ldvh-definition-text min-w-0 ${muted ? 'opacity-85' : ''}`}>
        <DefinitionValue value={String(value)} muted={muted} />
      </div>
    </WorkAreaSection>
  );
}

function WorkAreaMaterialSection({ fieldKey, value, locale }: { fieldKey: string; value: unknown; locale: string }) {
  if (!Array.isArray(value) || value.length === 0) return null;
  return (
    <WorkAreaSection title={getMaterialLabel(fieldKey, locale)}>
      <MaterialValue fieldKey={fieldKey} value={value} locale={locale} referenceVariant="plain" />
    </WorkAreaSection>
  );
}

function WorkAreaPlanGroup({
  title,
  tone,
  plans,
  locale,
  getStatus,
  onOpen,
  defaultCollapsed = false,
}: {
  title: string;
  tone: 'active' | 'review' | 'closed';
  plans: RelatedPlanSummary[];
  locale: string;
  getStatus: (status: string) => string;
  onOpen: (plan: RelatedPlanSummary) => void;
  defaultCollapsed?: boolean;
}) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const toneClass = {
    active: {
      section: 'border-emerald-500/30 bg-emerald-500/5',
      header: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
      row: 'hover:bg-emerald-500/10',
      icon: 'text-emerald-400',
      titleHover: 'group-hover/workarea-plan-row:text-emerald-400',
      iconHover: 'group-hover/workarea-plan-row:text-emerald-400 hover:text-emerald-400',
    },
    review: {
      section: 'border-violet-500/30 bg-violet-500/5',
      header: 'border-violet-500/30 bg-violet-500/10 text-violet-400',
      row: 'hover:bg-violet-500/10',
      icon: 'text-violet-400',
      titleHover: 'group-hover/workarea-plan-row:text-violet-400',
      iconHover: 'group-hover/workarea-plan-row:text-violet-400 hover:text-violet-400',
    },
    closed: {
      section: 'border-ldvh-border bg-ldvh-bg/60',
      header: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
      row: 'hover:bg-ldvh-border/35',
      icon: 'text-ldvh-text-secondary',
      titleHover: 'group-hover/workarea-plan-row:text-ldvh-accent',
      iconHover: 'group-hover/workarea-plan-row:text-ldvh-accent hover:text-ldvh-accent',
    },
  }[tone];
  const canCollapse = defaultCollapsed || tone === 'closed';
  const headerClassName = `ldvh-caption-strong flex w-full min-w-0 items-center gap-2 border px-3 py-2 text-left ${toneClass.header}`;
  const headerContent = (
    <>
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-80" aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate">{title}</span>
      {canCollapse && (collapsed ? <ChevronDown size={13} className="shrink-0" /> : <ChevronUp size={13} className="shrink-0" />)}
    </>
  );

  return (
    <div className={`min-w-0 overflow-hidden rounded-md border ${toneClass.section}`}>
      {canCollapse ? (
        <button type="button" onClick={() => setCollapsed((value) => !value)} className={`${headerClassName} cursor-pointer`}>
          {headerContent}
        </button>
      ) : (
        <div className={`${headerClassName} cursor-default`}>
          {headerContent}
        </div>
      )}
      {!collapsed && (
        <div className="divide-y divide-ldvh-border/60 px-1 py-1">
          {plans.map((plan) => (
            <WorkAreaPlanRow
              key={plan.id}
              plan={plan}
              locale={locale}
              getStatus={getStatus}
              toneClass={toneClass}
              onOpen={onOpen}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function WorkAreaPlanRow({
  plan,
  locale,
  getStatus,
  toneClass,
  onOpen,
}: {
  plan: RelatedPlanSummary;
  locale: string;
  getStatus: (status: string) => string;
  toneClass: { row: string; icon: string; titleHover: string; iconHover: string };
  onOpen: (plan: RelatedPlanSummary) => void;
}) {
  const { t } = useI18n();
  const { isOpen: panelOpen, content: panelContent } = usePanel();
  const open = () => onOpen(plan);
  const tasks = plan.tasks ?? [];
  const isCurrentPanelOpen = panelOpen && panelContent?.type === 'object' && panelContent.objectType === 'taskplan' && panelContent.objectId === plan.id;
  const PanelIcon = isCurrentPanelOpen ? PanelRightClose : PanelRightOpen;

  return (
    <div
      role="button"
      tabIndex={0}
      data-detail-object-id={plan.id}
      data-detail-object-type="taskplan"
      onClick={open}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          open();
        }
      }}
      className={`group/workarea-plan-row flex min-w-0 cursor-pointer flex-col gap-2 rounded-md px-2 py-2.5 text-left transition-colors ${toneClass.row}`}
    >
      <div className="flex min-w-0 items-start gap-3">
        <div className="min-w-0 flex-1">
          <span className={`ldvh-body flex min-w-0 items-center gap-1.5 truncate transition-colors ${toneClass.titleHover}`}>
            <PriorityIcon source={plan} type="taskplan" locale={locale} size="sm" />
            <ObjectTypeIcon type="taskplan" size={12} className="shrink-0" />
            <span className="min-w-0 truncate">{getLocalizedTitle(plan, locale)}</span>
          </span>
          <div className="mt-0.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
            <span className="ldvh-meta-muted min-w-0 truncate">{plan.id}</span>
            <span className="ldvh-caption">{formatDateTime(plan.updated)}</span>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <CopyPathButton
            path={plan.path}
            toneClassName="bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-text-secondary"
          />
          <PanelIcon
            size={14}
            aria-hidden="true"
            className={`text-ldvh-text-secondary/70 transition-colors ${isCurrentPanelOpen ? toneClass.icon : toneClass.iconHover}`}
          />
        </div>
      </div>
      {tasks.length > 0 && (
        <div className="min-w-0 self-stretch">
          <TaskFlowBar tasks={tasks} t={t} getStatus={getStatus} compact />
        </div>
      )}
    </div>
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

function getMaterialLabel(fieldKey: string, locale: string) {
  const labels: Record<string, { zh: string; en: string }> = {
    related_docs: { zh: '文档', en: 'Docs' },
    related_adrs: { zh: '决策', en: 'ADRs' },
    related_memos: { zh: '备忘', en: 'Memos' },
    related_pitfalls: { zh: '踩坑经验', en: 'Pitfalls' },
  };
  const entry = labels[fieldKey];
  if (!entry) return getFieldLabel(fieldKey, locale);
  return locale === 'en' ? entry.en : entry.zh;
}

/** 元信息小标签 */
function MetaChip({ label, value }: { label: string; value: ReactNode }) {
  const valueClassName = typeof value === 'string' ? 'ldvh-meta-primary min-w-0' : 'min-w-0';
  return (
    <div className="flex min-w-0 items-center gap-1.5 rounded-md border border-ldvh-border bg-ldvh-panel px-2.5 py-1">
      <span className="ldvh-caption shrink-0">{label}</span>
      <span className={valueClassName}>{value}</span>
    </div>
  );
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

export function TaskPlanReadingLayout({
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
  const tasks = sortPlanTasks(summary?.tasks ?? []);
  const relatedDocs = ((obj.aggregated_related_docs as string[] | undefined) ?? (obj.related_docs as string[] | undefined)) || [];
  const relatedAdrs = ((obj.aggregated_related_adrs as string[] | undefined) ?? (obj.related_adrs as string[] | undefined)) || [];
  const relatedMemos = ((obj.aggregated_related_memos as string[] | undefined) ?? (obj.related_memos as string[] | undefined)) || [];
  const relatedPitfalls = ((obj.aggregated_related_pitfalls as string[] | undefined) ?? (obj.related_pitfalls as string[] | undefined)) || [];
  const relatedChanges = ((obj.aggregated_related_changes as string[] | undefined) ?? (obj.related_changes as string[] | undefined)) || [];
  const hidden = new Set([
    ...META_KEYS,
    'workarea',
    'priority',
    'description',
    'success_criteria',
    'source',
    'tasks',
    'completion_evidence',
    'review_requested_at',
    'closed_at',
    'related_docs',
    'related_adrs',
    'related_memos',
    'related_pitfalls',
    'related_changes',
    'aggregated_deliverables',
    'aggregated_docs',
    'aggregated_related_docs',
    'aggregated_related_adrs',
    'aggregated_related_memos',
    'aggregated_related_pitfalls',
    'aggregated_related_changes',
  ]);
  const otherEntries = Object.entries(obj).filter(([key, value]) => !hidden.has(key) && hasDetailContent(value));

  return (
    <div className="mb-6 flex flex-col gap-5">
      <TaskSection title={t('objectDetail.planExecution')} tone="default">
        {loading ? (
          <LoadingHint text={t('objectDetail.tasksLoading')} />
        ) : tasks.length > 0 ? (
          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="mb-2 min-w-0">
              <TaskFlowBar tasks={tasks} t={t} getStatus={getStatus} />
            </div>
            <div className="divide-y divide-ldvh-border/60">
              {tasks.map((task) => (
                <DetailTaskRow
                  key={task.id}
                  item={task}
                  locale={locale}
                  getStatus={getStatus}
                  showSubtaskPosture
                />
              ))}
            </div>
          </div>
        ) : (
          <EmptyHint text={t('objectList.noTasks')} />
        )}
      </TaskSection>

      <TaskPlanCloseDecision
        successCriteria={obj.success_criteria}
        completionEvidence={obj.completion_evidence}
        locale={locale}
      />

      <DetailNarrativeSection title={t('objectDetail.workareaGoal')} value={obj.description} />
      <DetailObjectReferenceSection
        title={t('objectDetail.parentWorkArea')}
        item={summary?.workareaSummary}
        fallbackId={typeof obj.workarea === 'string' ? obj.workarea : undefined}
        objectType="workarea"
        locale={locale}
      />
      <DetailDefinitionSection title={getFieldLabel('source', locale)} value={obj.source} />
      <DetailMaterialSection fieldKey="related_docs" value={relatedDocs} locale={locale} />
      <DetailMaterialSection fieldKey="related_adrs" value={relatedAdrs} locale={locale} />
      <DetailMaterialSection fieldKey="related_memos" value={relatedMemos} locale={locale} />
      <DetailMaterialSection fieldKey="related_pitfalls" value={relatedPitfalls} locale={locale} />
      <DetailMaterialSection fieldKey="related_changes" value={relatedChanges} locale={locale} />

      {otherEntries.length > 0 && (
        <TaskSection title={t('objectDetail.otherFields')} tone="default">
          <div className="flex flex-col gap-3">
            {otherEntries.map(([key, value]) => (
              <ContentField key={key} fieldKey={key} value={value} locale={locale} objType="taskplan" />
            ))}
          </div>
        </TaskSection>
      )}
    </div>
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

function TaskPlanCloseDecision({
  successCriteria,
  completionEvidence,
  locale,
}: {
  successCriteria: unknown;
  completionEvidence: unknown;
  locale: string;
}) {
  const { t } = useI18n();
  const evidence = getChecklistProgress(completionEvidence);
  const hasCriteria = hasDetailContent(successCriteria);
  const hasEvidence = hasDetailContent(completionEvidence);

  return (
    <>
      <TaskSection title={getFieldLabel('success_criteria', locale)} tone="checklist">
        {hasCriteria ? <ChecklistCard value={String(successCriteria)} /> : <EmptyHint text={t('objectDetail.noSuccessCriteria')} />}
      </TaskSection>
      <TaskSection title={getFieldLabel('completion_evidence', locale)} tone="evidence">
        {hasEvidence
          ? evidence.total > 0
            ? <ChecklistCard value={String(completionEvidence)} />
            : <EvidenceBlock value={String(completionEvidence)} embedded />
          : <EmptyHint text={t('objectDetail.noCompletionEvidence')} />}
      </TaskSection>
    </>
  );
}

function DetailDefinitionSection({ title, value, muted = false }: { title: string; value: unknown; muted?: boolean }) {
  if (!hasDetailContent(value)) return null;
  return (
    <TaskSection title={title} tone="primary">
      <div className={`ldvh-definition-text min-w-0 ${muted ? 'opacity-85' : ''}`}>
        <DefinitionValue value={String(value)} muted={muted} />
      </div>
    </TaskSection>
  );
}

function DetailNarrativeSection({ title, value }: { title: string; value: unknown }) {
  if (!hasDetailContent(value)) return null;
  return (
    <TaskSection title={title} tone="primary">
      <SummaryText value={String(value)} collapseThreshold={900} />
    </TaskSection>
  );
}

function DetailDocumentSection({ title, docs }: { title: string; docs: string[] }) {
  if (docs.length === 0) return null;
  return (
    <TaskSection title={title} tone="docs">
      <DocumentOrTextList items={docs} fieldKey="related_docs" variant="plain" />
    </TaskSection>
  );
}

function DetailMaterialSection({ fieldKey, value, locale }: { fieldKey: string; value: unknown; locale: string }) {
  if (!Array.isArray(value) || value.length === 0) return null;
  return (
    <TaskSection title={getMaterialLabel(fieldKey, locale)} tone="default">
      <MaterialValue fieldKey={fieldKey} value={value} locale={locale} referenceVariant="plain" />
    </TaskSection>
  );
}

function DetailObjectReferenceSection({
  title,
  item,
  fallbackId,
  objectType,
  locale,
}: {
  title: string;
  item?: RelatedObjectSummary | ObjectItem | null;
  fallbackId?: string;
  objectType: string;
  locale: string;
}) {
  const objectId = item?.id ?? fallbackId;
  if (!objectId) return null;

  return (
    <TaskSection title={title} tone="primary">
      <DetailObjectReferenceValue
        item={item}
        fallbackId={fallbackId}
        objectType={objectType}
        locale={locale}
      />
    </TaskSection>
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
  currentTask: RelatedObjectSummary | null,
  parentPlan: ObjectItem | null,
): RelatedObjectSummary | null {
  if (currentTask?.id === refId) return currentTask;
  const planTasks = parentPlan?.tasks ?? [];
  const taskMatch = planTasks.find((task) => task.id === refId);
  if (taskMatch) return taskMatch;
  return [...(currentTask?.subtasks ?? []), ...planTasks.flatMap((task) => task.subtasks ?? [])]
    .find((subtask) => subtask.id === refId) ?? null;
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

export function TaskProgressSection({
  item,
  getStatus,
}: {
  item: RelatedObjectSummary;
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const flowTone = getTaskFlowTone(item);
  const flowLabel = getTaskFlowLabel(item, t, getStatus);

  return (
    <TaskSection title={t('objectDetail.taskProgress')} tone="default">
      <div className="flex min-w-0 flex-col gap-3">
        <div className={`flex min-w-0 items-center gap-2 rounded-md border px-3 py-2 ${taskFlowRowClass[flowTone]}`}>
          <TaskFlowMarker tone={flowTone} label={flowLabel} compact />
          <div className="min-w-0">
            <div className="ldvh-body min-w-0 truncate text-ldvh-text-primary">{flowLabel}</div>
          </div>
        </div>
      </div>
    </TaskSection>
  );
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
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const objectId = item?.id ?? fallbackId;
  if (!objectId) return null;

  const title = item ? getLocalizedTitle(item, locale) : objectId;
  const isCurrentPanelOpen = panelOpen && panelContent?.type === 'object' && panelContent.objectType === objectType && panelContent.objectId === objectId;
  const PanelIcon = isCurrentPanelOpen ? PanelRightClose : PanelRightOpen;
  const objectTypeColor = CATEGORY_COLORS[objectType] || CATEGORY_COLORS.other;
  const labelIcon = <ObjectTypeIcon type={objectType} size={12} className="shrink-0" style={{ color: objectTypeColor }} />;
  const open = () => openPanel({ type: 'object', title, objectType, objectId });
  const rowClassName = variant === 'property'
    ? 'group/detail-ref grid min-w-0 cursor-pointer gap-2 py-3 text-left transition-colors first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr]'
    : `group/detail-ref grid min-w-0 cursor-pointer gap-2 text-left transition-colors first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr] ${compact ? 'py-2' : 'py-3'}`;

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
        {variant !== 'property' && item?.status && <StatusBadge status={item.status} statusLabel={getObjectStatusLocale(objectType, item.status, locale)} size="sm" />}
        <CopyPathButton path={item?.path} />
        <PanelIcon size={14} className={`shrink-0 transition-colors ${isCurrentPanelOpen ? 'text-ldvh-accent' : 'text-ldvh-text-secondary group-hover/detail-ref:text-ldvh-accent'}`} />
      </div>
    </div>
  );
}

function DetailObjectReferenceValue({
  item,
  fallbackId,
  objectType,
  locale,
}: {
  item?: RelatedObjectSummary | ObjectItem | null;
  fallbackId?: string;
  objectType: string;
  locale: string;
}) {
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const objectId = item?.id ?? fallbackId;
  if (!objectId) return null;

  const title = item ? getLocalizedTitle(item, locale) : objectId;
  const isCurrentPanelOpen = panelOpen && panelContent?.type === 'object' && panelContent.objectType === objectType && panelContent.objectId === objectId;
  const PanelIcon = isCurrentPanelOpen ? PanelRightClose : PanelRightOpen;
  const objectTypeColor = CATEGORY_COLORS[objectType] || CATEGORY_COLORS.other;
  const open = () => openPanel({ type: 'object', title, objectType, objectId });

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
      className="group/detail-ref flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-ldvh-border/35"
    >
      <ObjectTypeIcon type={objectType} size={12} className="shrink-0" style={{ color: objectTypeColor }} />
      <span className="ldvh-body min-w-0 flex-1 truncate transition-colors group-hover/detail-ref:text-ldvh-accent">{title}</span>
      <CopyPathButton path={item?.path} />
      <PanelIcon size={14} className={`shrink-0 transition-colors ${isCurrentPanelOpen ? 'text-ldvh-accent' : 'text-ldvh-text-secondary group-hover/detail-ref:text-ldvh-accent'}`} />
    </div>
  );
}

export function DetailTaskRow({
  item,
  locale,
  getStatus,
  showSubtaskPosture = false,
}: {
  item: RelatedObjectSummary;
  locale: string;
  getStatus: (status: string) => string;
  showSubtaskPosture?: boolean;
}) {
  const { t } = useI18n();
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const flowTone = getTaskFlowTone(item);
  const flowLabel = getTaskFlowLabel(item, t, getStatus);
  const subtasks = item.subtasks ?? [];
  const objectType = item.type || 'task';
  const title = getLocalizedTitle(item, locale);
  const isCurrentPanelOpen = panelOpen && panelContent?.type === 'object' && panelContent.objectType === objectType && panelContent.objectId === item.id;
  const PanelIcon = isCurrentPanelOpen ? PanelRightClose : PanelRightOpen;
  const open = () => openPanel({ type: 'object', title, objectType, objectId: item.id });

  return (
    <div className="py-1 first:pt-0 last:pb-0">
      <div
        role="button"
        tabIndex={0}
        data-detail-object-id={item.id}
        data-detail-object-type={objectType}
        onClick={open}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            open();
          }
        }}
        className={`group/detail-task min-w-0 cursor-pointer rounded-md border px-2 py-2 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ldvh-accent/70 ${taskFlowRowClass[flowTone]}`}
      >
        <div className="flex min-w-0 items-center gap-2">
          <TaskFlowMarker tone={flowTone} label={flowLabel} compact={objectType === 'subtask'} />
          <div className="min-w-0 flex-1">
            <span className={`ldvh-body flex min-w-0 items-center gap-1.5 truncate transition-colors ${taskFlowDetailHoverTextClass[flowTone]}`}>
              <ObjectTypeIcon type={objectType} size={12} className="shrink-0" />
              <span className="min-w-0 truncate">{title}</span>
            </span>
            <span className="ldvh-meta-muted block min-w-0 truncate">{item.id}</span>
          </div>
          <CopyPathButton path={item.path} toneClassName={taskFlowDetailActionClass[flowTone]} />
          <PanelIcon size={14} className={`shrink-0 text-ldvh-text-secondary/70 transition-colors ${taskFlowDetailHoverTextClass[flowTone]}`} />
        </div>
        {showSubtaskPosture && subtasks.length > 0 && (
          <div className="ml-9 mt-2 min-w-0">
            <TaskFlowBar tasks={subtasks} t={t} getStatus={getStatus} compact />
          </div>
        )}
      </div>
    </div>
  );
}

export function TaskReadingLayout({
  obj,
  locale,
  objType,
  summary,
  parentPlan,
  loading,
  getStatus,
}: {
  obj: Record<string, unknown>;
  locale: string;
  objType: string;
  summary: RelatedObjectSummary | null;
  parentPlan: ObjectItem | null;
  loading: boolean;
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const hidden = new Set([
    'source',
    'description',
    'taskplan',
    'task',
    'acceptance',
    'verification',
    'closure_evidence',
    'deliverables',
    'related_docs',
    'affected_docs',
    'related_adrs',
    'related_changes',
    'blocked_by',
    'status_history',
    ...TASK_AUXILIARY_META_KEYS,
    ...META_KEYS,
  ]);
  const otherEntries = Object.entries(obj).filter(([key, value]) => !hidden.has(key) && hasDetailContent(value));
  const subtasks = sortPlanTasks(summary?.subtasks ?? []);
  const showSubtasks = objType === 'task' && (loading || subtasks.length > 0);
  const currentSummary = objType === 'subtask'
    ? summary?.subtasks?.find((subtask) => subtask.id === obj.id) ?? null
    : summary;
  const currentFlowItem = buildCurrentFlowItem(obj, objType, locale, currentSummary);
  const verificationValue = hasDetailContent(obj.verification) ? String(obj.verification) : '';
  const deliverables = (obj.deliverables as string[] | undefined) ?? [];
  const relatedDocs = (obj.related_docs as string[] | undefined) ?? [];
  const affectedDocs = (obj.affected_docs as string[] | undefined) ?? [];

  return (
    <div className="mb-6 flex flex-col gap-5">
      <TaskProgressSection
        item={currentFlowItem}
        getStatus={getStatus}
      />

      {showSubtasks && (
        <TaskSection title={t('objectDetail.subtaskExecution')} tone="default">
          {loading ? (
            <LoadingHint text={t('objectDetail.subtasksLoading')} />
          ) : (
            <div className="flex min-w-0 flex-col gap-3">
              <TaskFlowBar tasks={subtasks} t={t} getStatus={getStatus} />
              <div className="divide-y divide-ldvh-border/60">
                {subtasks.map((subtask) => (
                  <DetailTaskRow key={subtask.id} item={subtask} locale={locale} getStatus={getStatus} />
                ))}
              </div>
            </div>
          )}
        </TaskSection>
      )}

      <TaskSection title={getFieldLabel('acceptance', locale)} tone="checklist">
        {obj.acceptance ? <ChecklistCard value={String(obj.acceptance)} /> : <EmptyHint text={t('objectDetail.noAcceptance')} />}
      </TaskSection>

      <TaskSection title={getFieldLabel('verification', locale)} tone={verificationValue && hasChecklist(verificationValue) ? 'checklist' : 'evidence'}>
        {verificationValue
          ? (hasChecklist(verificationValue) ? <ChecklistCard value={verificationValue} /> : <EvidenceBlock value={verificationValue} embedded />)
          : <EmptyHint text={t('objectDetail.noVerification')} />}
      </TaskSection>

      <DetailNarrativeSection title={t('objectDetail.workareaGoal')} value={obj.description} />
      {obj.taskplan && (
        <DetailObjectReferenceSection
          title={t('objectDetail.taskPlan')}
          item={parentPlan}
          fallbackId={String(obj.taskplan)}
          objectType="taskplan"
          locale={locale}
        />
      )}
      {obj.task && (
        <DetailObjectReferenceSection
          title={getFieldLabel('task', locale)}
          item={summary}
          fallbackId={String(obj.task)}
          objectType="task"
          locale={locale}
        />
      )}
      <DetailDefinitionSection title={getFieldLabel('source', locale)} value={obj.source} />
      {hasDetailContent(obj.closure_evidence) && (
        <TaskSection title={getFieldLabel('closure_evidence', locale)} tone="evidence">
          <EvidenceBlock value={String(obj.closure_evidence)} embedded />
        </TaskSection>
      )}

      <DetailDocumentSection title={t('objectDetail.deliverables')} docs={deliverables} />
      <DetailMaterialSection fieldKey="related_docs" value={relatedDocs} locale={locale} />
      <DetailDocumentSection title={t('objectDetail.affectedDocs')} docs={affectedDocs} />
      <DetailMaterialSection fieldKey="related_adrs" value={obj.related_adrs} locale={locale} />
      <DetailMaterialSection fieldKey="related_changes" value={obj.related_changes} locale={locale} />

      {otherEntries.length > 0 && (
        <TaskSection title={t('objectDetail.otherFields')} tone="default">
          <div className="flex flex-col gap-3">
            {otherEntries.map(([key, value]) => (
              <ContentField key={key} fieldKey={key} value={value} locale={locale} objType={objType} />
            ))}
          </div>
        </TaskSection>
      )}
    </div>
  );
}

function getAuxiliaryMetaEntries(obj: Record<string, unknown>, objType: string) {
  const keys = Array.from(new Set([...(AUXILIARY_META_KEYS_BY_TYPE[objType] || []), ...COMMON_AUXILIARY_META_KEYS]));
  return keys
    .filter((key) => key !== 'priority' || (objType !== 'taskplan' && objType !== 'memo'))
    .map((key) => [key, obj[key]] as [string, unknown])
    .filter(([, value]) => value !== null && value !== undefined && value !== '' && (!Array.isArray(value) || value.length > 0));
}

export function getFieldLabel(fieldKey: string, locale: string) {
  const labelEntry = FIELD_LABEL_LOCALES[fieldKey];
  return labelEntry ? (locale === 'en' ? labelEntry.en : labelEntry.zh) : fieldKey.replace(/_/g, ' ');
}

function localizeMetaValue(fieldKey: string, rawValue: string, locale: string) {
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

export function TaskSection({
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
  const toneClass = {
    primary: 'border-ldvh-border bg-ldvh-panel',
    checklist: 'border-ldvh-border bg-ldvh-panel',
    evidence: 'border-ldvh-border bg-ldvh-panel',
    docs: 'border-ldvh-border bg-ldvh-panel',
    default: 'border-ldvh-border bg-ldvh-panel',
  }[tone];

  return (
    <section className={`rounded-xl border p-4 ${toneClass}`}>
      <h2 className="ldvh-section-title mb-3 flex min-w-0 items-center gap-2">
        {icon ?? <span className="h-1.5 w-1.5 rounded-full bg-ldvh-accent" />}
        <span className="min-w-0 truncate">{title}</span>
      </h2>
      {children}
    </section>
  );
}

export function TaskInlineField({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="grid gap-2 py-3 first:pt-0 last:pb-0 sm:grid-cols-[5.625rem_1fr]">
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{label}</div>
      <div className="min-w-0">{value}</div>
    </div>
  );
}

export function TaskDocGroup({ label, docs }: { label: string; docs?: string[] }) {
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
export function ContentField({ fieldKey, value, locale, objType }: { fieldKey: string; value: unknown; locale: string; objType: string }) {
  const isCollapsible = COLLAPSIBLE_FIELDS.includes(fieldKey);
  const [collapsed, setCollapsed] = useState(isCollapsible ? objType !== 'taskplan' : false);

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

/** 从引用 ID 解析对象类型（如 task-0001 → task） */
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
