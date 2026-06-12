import { useEffect, useRef, useState, useCallback } from 'react';
import { ChevronLeft, ChevronRight, X, GripVertical, FileText, FileDiff } from 'lucide-react';
import { usePanel, type PanelContent } from '@/utils/panelContext';
import ChecklistCard from '@/components/ChecklistCard';
import DocPreviewLink from '@/components/DocPreviewLink';
import EvidenceBlock from '@/components/EvidenceBlock';
import MarkdownPreview from '@/components/MarkdownPreview';
import ReferenceCard from '@/components/ReferenceCard';
import StatusBadge from '@/components/StatusBadge';
import SummaryText from '@/components/SummaryText';
import CopyPathButton from '@/components/CopyPathButton';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale } from '@/i18n/locales';
import { fetchDocContent, fetchObjectDetail, type DocContent, type ObjectDetail as ApiObjectDetail } from '@/utils/api';
import {
  CHECKLIST_COMPAT_FIELDS,
  DOC_LINK_FIELDS,
  EVIDENCE_FIELDS,
  REFERENCE_FIELDS,
  SUMMARY_TEXT_FIELDS,
  hasChecklist,
  isObjectRef,
  isPreviewableDocPath,
} from '@/utils/fieldFormats';

const MIN_WIDTH = 280;
const MAX_WIDTH_RATIO = 0.58;
const DEFAULT_WIDTH = 380;
const DEFAULT_DOC_WIDTH = 680;
const SNAP_THRESHOLD = 40;
const MOBILE_BREAKPOINT = 768;

const PREVIEW_FIELD_ORDER_BY_TYPE: Record<string, string[]> = {
  workarea: [
    'description', 'source', 'scope', 'constraints', 'related_docs',
    'related_adrs', 'related_memos', 'related_pitfalls', 'archive_reason',
    'status_history',
  ],
  taskplan: [
    'workarea', 'description', 'success_criteria', 'source', 'tasks',
    'completion_evidence', 'review_requested_at', 'related_docs',
    'related_adrs', 'related_memos', 'related_pitfalls', 'status_history',
  ],
  task: [
    'taskplan', 'description', 'source', 'acceptance', 'verification',
    'risk_assessment', 'closure_evidence', 'blocked_by',
    'deliverables', 'related_docs', 'affected_docs', 'related_adrs',
    'related_changes', 'status_history',
  ],
  subtask: [
    'task', 'description', 'source', 'acceptance', 'verification',
    'closure_evidence', 'blocked_by', 'status_history',
  ],
  adr: [
    'context', 'decision', 'consequences', 'alternatives', 'affects',
    'related_tasks', 'related_taskplans', 'related_workareas', 'related_memos', 'related_rules',
    'superseded_by', 'status_history',
  ],
  pitfall: [
    'symptoms', 'trigger_conditions', 'root_cause', 'resolution', 'verification',
    'avoidance', 'applicability', 'source_objects', 'source_tasks',
    'source_memos', 'related_workareas', 'related_taskplans', 'related_adrs', 'related_rules',
    'superseded_by', 'archive_reason', 'status_history', 'notes',
  ],
  memo: [
    'description', 'source', 'archive_reason', 'resolved_to', 'related_tasks',
    'related_taskplans', 'related_workareas', 'related_adrs', 'related_docs', 'status_history',
  ],
  profile: [
    'description', 'project_path', 'ldvh_base_path', 'docs_path',
    'governance_scope', 'related_workareas', 'related_taskplans', 'related_tasks', 'related_adrs',
    'related_memos', 'related_pitfalls', 'related_docs', 'status_history',
    'notes',
  ],
};

const PREVIEW_META_KEYS = new Set([
  'id', 'type', 'title', 'title_en', 'title_zh', 'status', 'created', 'updated',
  'closed_at', 'review_requested_at', 'resolved_at', 'category', 'priority', 'severity',
  'repeatability', 'tags', 'assignee', 'scope', 'impact',
]);

const PREVIEW_FIELD_LABELS: Record<string, { zh: string; en: string }> = {
  description: { zh: '描述', en: 'Description' },
  summary: { zh: '摘要', en: 'Summary' },
  details: { zh: '详情', en: 'Details' },
  background: { zh: '背景', en: 'Background' },
  motivation: { zh: '动机', en: 'Motivation' },
  outcome: { zh: '结果', en: 'Outcome' },
  next_steps: { zh: '后续步骤', en: 'Next Steps' },
  lessons: { zh: '经验教训', en: 'Lessons' },
  source: { zh: '来源', en: 'Source' },
  workarea: { zh: '工作域', en: 'Work Area' },
  taskplan: { zh: '任务计划', en: 'Task Plan' },
  task: { zh: '所属任务', en: 'Task' },
  tasks: { zh: '任务', en: 'Tasks' },
  success_criteria: { zh: '成功标准', en: 'Success Criteria' },
  constraints: { zh: '约束', en: 'Constraints' },
  acceptance: { zh: '验收标准', en: 'Acceptance' },
  verification: { zh: '验证方式', en: 'Verification' },
  risk_assessment: { zh: '风险判断', en: 'Risk Assessment' },
  closure_evidence: { zh: '关闭证据', en: 'Closure Evidence' },
  completion_evidence: { zh: '完成证据', en: 'Completion Evidence' },
  review_requested_at: { zh: '请求关闭确认时间', en: 'Review Requested At' },
  blocked_by: { zh: '前置依赖', en: 'Blocked By' },
  deliverables: { zh: '产出物', en: 'Deliverables' },
  related_docs: { zh: '关联文档', en: 'Related Docs' },
  affected_docs: { zh: '受影响文档', en: 'Affected Docs' },
  related_tasks: { zh: '关联任务', en: 'Related Tasks' },
  related_subtasks: { zh: '关联子任务', en: 'Related Subtasks' },
  related_workareas: { zh: '关联工作域', en: 'Related Work Areas' },
  related_taskplans: { zh: '关联任务计划', en: 'Related Task Plans' },
  related_adrs: { zh: '关联 ADR', en: 'Related ADRs' },
  related_memos: { zh: '关联备忘', en: 'Related Memos' },
  related_pitfalls: { zh: '关联踩坑', en: 'Related Pitfalls' },
  related_profiles: { zh: '关联画像', en: 'Related Profiles' },
  related_rules: { zh: '承接规则', en: 'Related Rules' },
  related_changes: { zh: '关联变更', en: 'Related Changes' },
  context: { zh: '背景', en: 'Context' },
  decision: { zh: '决策', en: 'Decision' },
  consequences: { zh: '影响', en: 'Consequences' },
  alternatives: { zh: '替代方案', en: 'Alternatives' },
  affects: { zh: '影响对象', en: 'Affects' },
  superseded_by: { zh: '替代来源', en: 'Superseded By' },
  symptoms: { zh: '问题现象', en: 'Symptoms' },
  trigger_conditions: { zh: '触发条件', en: 'Trigger Conditions' },
  root_cause: { zh: '根因', en: 'Root Cause' },
  resolution: { zh: '解决方案', en: 'Resolution' },
  avoidance: { zh: '规避策略', en: 'Avoidance' },
  applicability: { zh: '适用范围', en: 'Applicability' },
  source_objects: { zh: '来源对象', en: 'Source Objects' },
  source_tasks: { zh: '来源任务', en: 'Source Tasks' },
  source_memos: { zh: '来源备忘', en: 'Source Memos' },
  archive_reason: { zh: '归档原因', en: 'Archive Reason' },
  resolved_to: { zh: '分流目标', en: 'Resolved To' },
  status_history: { zh: '状态记录', en: 'Status History' },
  notes: { zh: '备注', en: 'Notes' },
  project_path: { zh: '项目路径', en: 'Project Path' },
  ldvh_base_path: { zh: '事实实例路径', en: 'LDVH Base Path' },
  docs_path: { zh: '文档路径', en: 'Docs Path' },
  governance_scope: { zh: '管辖范围', en: 'Governance Scope' },
  at: { zh: '时间', en: 'At' },
  from: { zh: '前状态', en: 'From' },
  to: { zh: '后状态', en: 'To' },
  actor: { zh: '执行者', en: 'Actor' },
  reason: { zh: '原因', en: 'Reason' },
};

const OBJECT_TYPE_LABELS: Record<string, { zh: string; en: string }> = {
  workarea: { zh: '工作域', en: 'Work Area' },
  taskplan: { zh: '任务计划', en: 'Task Plan' },
  task: { zh: '任务', en: 'Task' },
  subtask: { zh: '子任务', en: 'Subtask' },
  adr: { zh: 'ADR', en: 'ADR' },
  pitfall: { zh: '踩坑', en: 'Pitfall' },
  memo: { zh: '备忘', en: 'Memo' },
  profile: { zh: '画像', en: 'Profile' },
  change: { zh: '变更', en: 'Change' },
};

export default function ReadingPanel() {
  const { isOpen, content, canGoBack, canGoForward, goBack, goForward, closePanel } = usePanel();
  const { t } = useI18n();
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isDragging, setIsDragging] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [bottomSheetHeight, setBottomSheetHeight] = useState(50);
  const [draggingSheet, setDraggingSheet] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(DEFAULT_WIDTH);
  const startYRef = useRef(0);
  const startHeightRef = useRef(50);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  const maxWidth = Math.floor(window.innerWidth * MAX_WIDTH_RATIO);
  const clamp = useCallback(
    (w: number) => Math.max(MIN_WIDTH, Math.min(w, maxWidth)),
    [maxWidth],
  );

  useEffect(() => {
    if (!isMobile && content?.type === 'doc') {
      setWidth((prev) => clamp(Math.max(prev, DEFAULT_DOC_WIDTH)));
    }
  }, [clamp, content?.type, isMobile]);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startXRef.current = e.clientX;
    startWidthRef.current = width;
  }, [width]);

  useEffect(() => {
    if (!isDragging) return;
    const onMouseMove = (e: MouseEvent) => {
      const dx = startXRef.current - e.clientX;
      let newW = startWidthRef.current + dx;
      if (newW > maxWidth - SNAP_THRESHOLD) newW = maxWidth;
      if (newW < MIN_WIDTH + SNAP_THRESHOLD) newW = MIN_WIDTH;
      setWidth(clamp(newW));
    };
    const onMouseUp = () => {
      setIsDragging(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, clamp, maxWidth]);

  useEffect(() => {
    const onResize = () => {
      setWidth(prev => Math.min(prev, Math.floor(window.innerWidth * MAX_WIDTH_RATIO)));
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [clamp]);

  // Bottom sheet drag handlers
  const onSheetHandleDown = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    setDraggingSheet(true);
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    startYRef.current = clientY;
    startHeightRef.current = bottomSheetHeight;
  }, [bottomSheetHeight]);

  useEffect(() => {
    if (!draggingSheet) return;
    const onMove = (e: MouseEvent | TouchEvent) => {
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      const dy = startYRef.current - clientY;
      const vh = window.innerHeight;
      const newH = Math.max(20, Math.min(95, startHeightRef.current + (dy / vh) * 100));
      setBottomSheetHeight(newH);
    };
    const onUp = () => {
      setDraggingSheet(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      // Snap close if dragged below 30%
      if (bottomSheetHeight < 30) closePanel();
    };
    document.body.style.cursor = 'ns-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    document.addEventListener('touchmove', onMove);
    document.addEventListener('touchend', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.removeEventListener('touchmove', onMove);
      document.removeEventListener('touchend', onUp);
    };
  }, [draggingSheet, bottomSheetHeight, closePanel]);

  if (!isOpen && !content) return null;

  const panelTitle = content?.title || t('readingPanel.title');
  const preview = content ? <PanelContentRenderer content={content} /> : <EmptyPanelPreview />;

  if (isMobile && !isOpen) return null;

  const navigationControls = (
    <div className="flex shrink-0 items-center gap-1">
      <button
        type="button"
        onClick={goBack}
        disabled={!canGoBack}
        className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary disabled:cursor-default disabled:opacity-35"
        title={t('readingPanel.previous')}
        aria-label={t('readingPanel.previous')}
      >
        <ChevronLeft size={14} />
      </button>
      <button
        type="button"
        onClick={goForward}
        disabled={!canGoForward}
        className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary disabled:cursor-default disabled:opacity-35"
        title={t('readingPanel.next')}
        aria-label={t('readingPanel.next')}
      >
        <ChevronRight size={14} />
      </button>
    </div>
  );

  // Mobile: bottom sheet
  if (isMobile) {
    return (
      <>
        <div className="fixed inset-0 z-40 bg-black/40" onClick={closePanel} />
        <div
          ref={panelRef}
          className="fixed bottom-0 left-0 right-0 z-50 flex flex-col rounded-t-xl border-t border-ldvh-border bg-ldvh-panel shadow-lg shadow-black/20 transition-transform duration-300 ease-out"
          style={{ height: `${bottomSheetHeight}vh` }}
        >
          <div
            className="flex h-10 flex-shrink-0 cursor-ns-resize items-center justify-center border-b border-ldvh-border"
            onMouseDown={onSheetHandleDown}
            onTouchStart={onSheetHandleDown}
          >
            <div className="h-1 w-10 rounded-full bg-ldvh-border" />
          </div>
          <div className="flex items-center justify-between gap-2 px-4 py-2">
            <div className="flex min-w-0 flex-1 items-center gap-2">
              {navigationControls}
              <h3 className="ldvh-card-title truncate">{panelTitle}</h3>
            </div>
            <button
              type="button"
              onClick={closePanel}
              title={t('readingPanel.close')}
              aria-label={t('readingPanel.close')}
              className="rounded p-1 text-ldvh-text-secondary hover:bg-ldvh-border/30"
            >
              <X size={14} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {preview}
          </div>
        </div>
      </>
    );
  }

  // Desktop: right panel
  return (
    <div
      ref={panelRef}
      className={`relative flex-shrink-0 border-l border-ldvh-border bg-ldvh-panel transition-[width,opacity] duration-200 ease-in-out ${
        isOpen ? 'opacity-100' : 'w-0 overflow-hidden opacity-0 border-l-0'
      }`}
      style={{ width: isOpen ? width : 0 }}
    >
      <div
        className="absolute left-0 top-0 z-10 flex h-full w-2 cursor-col-resize items-center justify-center transition-colors hover:bg-ldvh-accent/20"
        onMouseDown={onMouseDown}
      >
        <div className="flex h-12 w-1.5 flex-col items-center justify-center rounded-full bg-ldvh-border/50 opacity-0 transition-opacity hover:opacity-100" />
      </div>
      <div className="flex items-center justify-between gap-2 border-b border-ldvh-border px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <GripVertical size={14} className="flex-shrink-0 text-ldvh-text-secondary" />
          {navigationControls}
          <h3 className="ldvh-card-title truncate">{panelTitle}</h3>
        </div>
        <button
          type="button"
          onClick={closePanel}
          title={t('readingPanel.close')}
          aria-label={t('readingPanel.close')}
          className="rounded p-1 text-ldvh-text-secondary hover:bg-ldvh-border/30"
        >
          <X size={14} />
        </button>
      </div>
      <div className="h-[calc(100%-49px)] overflow-y-auto p-4">
        {preview}
      </div>
    </div>
  );
}

function EmptyPanelPreview() {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="ldvh-body-muted">{t('readingPanel.empty')}</p>
    </div>
  );
}

function PanelContentRenderer({ content }: { content: PanelContent }) {
  switch (content.type) {
    case 'object': return <ObjectPreview content={content} />;
    case 'doc': return <DocPreview content={content} />;
    case 'yaml': return <YamlPreview content={content} />;
    case 'evidence': return <EvidencePreview content={content} />;
    case 'diff': return <DiffPreview content={content} />;
    default:
      return (
        <EmptyPanelPreview />
      );
  }
}

function ObjectPreview({ content }: { content: PanelContent }) {
  const { objectType, objectId, data } = content;
  const { locale, t } = useI18n();
  const [detail, setDetail] = useState<ApiObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const obj = (data as Record<string, unknown> | undefined) ?? detail?.data;
  const status = detail?.summary.status ?? (obj?.status as string | undefined);
  const title = getObjectTitle(obj, objectId, locale);
  const targetPath = detail?.target;
  const loading = !obj && !error && Boolean(objectType && objectId);

  useEffect(() => {
    if (data || !objectType || !objectId) {
      setDetail(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setDetail(null);
    setError(null);
    fetchObjectDetail(objectType, objectId)
      .then((result) => {
        if (!cancelled) setDetail(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    return () => {
      cancelled = true;
    };
  }, [data, objectType, objectId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-500/20 bg-red-500/10 p-3">
        <p className="ldvh-body text-red-300">{t('readingPanel.loadFailed')}</p>
        <p className="ldvh-meta mt-1 text-red-300/80">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="ldvh-chip rounded bg-ldvh-accent/20 px-2 py-0.5 text-ldvh-accent">
          {getObjectTypeLabel(objectType, locale)}
        </span>
        {status && <StatusBadge status={status} statusLabel={getObjectStatusLocale(objectType, status, locale)} size="sm" />}
        <CopyPathButton path={targetPath} className="ml-auto" />
      </div>
      <h3 className="ldvh-reading-title">{title}</h3>
      {objectId && <p className="ldvh-meta">{objectId}</p>}
      {obj && <SemanticObjectPreview objectType={objectType} obj={obj} />}
    </div>
  );
}

function getObjectTitle(obj: Record<string, unknown> | undefined, objectId: string | undefined, locale: string) {
  if (!obj) return objectId || '—';
  if (locale === 'en') {
    return (obj.title_en as string) || (obj.title as string) || objectId || '—';
  }
  return (obj.title_zh as string) || (obj.title as string) || objectId || '—';
}

function getObjectTypeLabel(objectType: string | undefined, locale: string) {
  if (!objectType) return '—';
  const labels = OBJECT_TYPE_LABELS[objectType];
  if (!labels) return objectType;
  return locale === 'en' ? labels.en : labels.zh;
}

function SemanticObjectPreview({ objectType, obj }: { objectType?: string; obj: Record<string, unknown> }) {
  const entries = getPreviewEntries(objectType, obj);
  if (entries.length === 0) return null;

  return (
    <div className="space-y-3">
      {entries.map(([fieldKey, value]) => (
        <PreviewField key={fieldKey} fieldKey={fieldKey} value={value} />
      ))}
    </div>
  );
}

function getPreviewEntries(objectType: string | undefined, obj: Record<string, unknown>) {
  const order = objectType ? PREVIEW_FIELD_ORDER_BY_TYPE[objectType] || [] : [];
  const orderedKeys = order.filter((key) => hasPreviewValue(obj[key]));
  const orderedSet = new Set(orderedKeys);
  const restEntries = Object.entries(obj).filter(
    ([key, value]) => !orderedSet.has(key) && !PREVIEW_META_KEYS.has(key) && hasPreviewValue(value),
  );

  return [
    ...orderedKeys.map((key) => [key, obj[key]] as [string, unknown]),
    ...restEntries,
  ];
}

function hasPreviewValue(value: unknown) {
  if (value === null || value === undefined || value === '') return false;
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

function PreviewField({ fieldKey, value }: { fieldKey: string; value: unknown }) {
  const { locale } = useI18n();
  return (
    <PreviewSection title={getPreviewFieldLabel(fieldKey, locale)}>
      <PreviewValue fieldKey={fieldKey} value={value} depth={0} />
    </PreviewSection>
  );
}

function PreviewValue({ fieldKey, value, depth }: { fieldKey: string; value: unknown; depth: number }) {
  const { t, locale } = useI18n();

  if (value === null || value === undefined || value === '') {
    return <EmptyPreview text={t('objectDetail.emptyValue')} />;
  }

  if (typeof value === 'string') {
    if (fieldKey === 'acceptance') {
      return <ChecklistCard value={value} />;
    }

    if (CHECKLIST_COMPAT_FIELDS.includes(fieldKey) && hasChecklist(value)) {
      return <ChecklistCard value={value} />;
    }

    if (DOC_LINK_FIELDS.includes(fieldKey) && isPreviewableDocPath(value)) {
      return <DocPreviewLink docs={[value]} />;
    }

    if (EVIDENCE_FIELDS.includes(fieldKey)) {
      return <EvidenceBlock value={value} embedded />;
    }

    if (REFERENCE_FIELDS.includes(fieldKey) && isObjectRef(value)) {
      return <ReferenceCard refs={[value]} />;
    }

    if (SUMMARY_TEXT_FIELDS.includes(fieldKey) || value.includes('\n') || value.length > 160) {
      return <PreviewText value={value} />;
    }

    return <span className="ldvh-body">{value}</span>;
  }

  if (typeof value === 'boolean') {
    return (
      <span className={`ldvh-chip rounded px-1.5 py-0.5 ${value ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
        {value ? t('common.true') : t('common.false')}
      </span>
    );
  }

  if (typeof value === 'number') {
    return <span className="ldvh-meta-primary text-ldvh-accent">{value}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <EmptyPreview text={t('common.empty')} />;
    if (typeof value[0] === 'string') {
      return <PreviewReferenceList fieldKey={fieldKey} items={value as string[]} />;
    }

    return (
      <div className="space-y-2">
        {value.map((item, index) => (
          <div key={index} className="rounded-md border border-ldvh-border bg-ldvh-panel p-2.5">
            <PreviewValue fieldKey={fieldKey} value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).filter(([, v]) => hasPreviewValue(v));
    if (entries.length === 0) return <EmptyPreview text={t('common.empty')} />;

    return (
      <div className="space-y-2">
        {entries.map(([key, nestedValue]) => (
          <div key={key} className="flex gap-2">
            <span className="ldvh-caption shrink-0 rounded border border-ldvh-border bg-ldvh-bg px-1.5 py-0.5">
              {getPreviewFieldLabel(key, locale)}
            </span>
            <div className="min-w-0 flex-1">
              <PreviewValue fieldKey={key} value={nestedValue} depth={depth + 1} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <span className="ldvh-body">{String(value)}</span>;
}

function PreviewReferenceList({ fieldKey, items }: { fieldKey: string; items: string[] }) {
  const docs = items.filter(isPreviewableDocPath);
  const objectRefs = items.filter(isObjectRef);
  const rest = items.filter((item) => !isPreviewableDocPath(item) && !isObjectRef(item));
  const shouldPreferDocs = DOC_LINK_FIELDS.includes(fieldKey);
  const shouldPreferRefs = REFERENCE_FIELDS.includes(fieldKey);

  if (shouldPreferDocs || shouldPreferRefs) {
    return (
      <div className="space-y-2">
        {objectRefs.length > 0 && <ReferenceCard refs={objectRefs} />}
        {docs.length > 0 && <DocPreviewLink docs={docs} />}
        {rest.length > 0 && <PreviewStringList items={rest} />}
      </div>
    );
  }

  return <PreviewStringList items={items} />;
}

function PreviewStringList({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, index) => (
        <span key={`${item}-${index}`} className="ldvh-chip rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-0.5 text-ldvh-text-primary">
          {item}
        </span>
      ))}
    </div>
  );
}

function getPreviewFieldLabel(fieldKey: string, locale: string) {
  const label = PREVIEW_FIELD_LABELS[fieldKey];
  if (label) return locale === 'en' ? label.en : label.zh;
  return fieldKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function PreviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-md border border-ldvh-border bg-ldvh-bg p-3">
      <PreviewLabel>{title}</PreviewLabel>
      <div className="mt-2">{children}</div>
    </section>
  );
}

function PreviewLabel({ children }: { children: React.ReactNode }) {
  return <p className="ldvh-caption-strong">{children}</p>;
}

function PreviewText({ value }: { value: string }) {
  return <SummaryText value={value} />;
}

function EmptyPreview({ text }: { text: string }) {
  return <span className="ldvh-body-muted italic">{text}</span>;
}

function DocPreview({ content }: { content: PanelContent }) {
  const { t } = useI18n();
  const { docPath, data } = content;
  const [doc, setDoc] = useState<DocContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const docContent = typeof data === 'string' ? data : doc?.content ?? '';
  const truncated = doc?.truncated ?? false;
  const isMarkdown = Boolean(docPath && /\.(md|markdown)$/i.test(docPath));

  useEffect(() => {
    if (typeof data === 'string' || !docPath) {
      setDoc(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setDoc(null);
    setError(null);
    fetchDocContent(docPath)
      .then((result) => {
        if (!cancelled) setDoc(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });

    return () => {
      cancelled = true;
    };
  }, [data, docPath]);

  if (error) {
    return (
      <div className="space-y-3">
        <div className="rounded-md border border-red-500/20 bg-red-500/10 p-3">
          <p className="ldvh-body text-red-300">{t('readingPanel.docLoadFailed')}</p>
          <p className="ldvh-meta mt-1 text-red-300/80">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {!docContent ? (
        <div className="flex items-center justify-center rounded-md bg-ldvh-bg py-16">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
        </div>
      ) : isMarkdown ? (
        <article className="rounded-lg border border-ldvh-border bg-ldvh-panel px-4 py-4 shadow-sm shadow-black/10">
          <MarkdownPreview content={docContent} />
          {truncated && <p className="ldvh-caption mt-3">{t('readingPanel.truncated')}</p>}
        </article>
      ) : (
        <div className="rounded-md bg-ldvh-bg p-3">
          <pre className="ldvh-meta-primary whitespace-pre-wrap">
            {docContent}
          </pre>
          {truncated && <p className="ldvh-caption mt-3">{t('readingPanel.truncated')}</p>}
        </div>
      )}
    </div>
  );
}

function YamlPreview({ content }: { content: PanelContent }) {
  const { data } = content;
  const yamlText = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  return (
    <div className="space-y-3">
      <div className="rounded-md bg-ldvh-bg p-3">
        <pre className="ldvh-meta-primary max-h-[600px] overflow-y-auto whitespace-pre-wrap">
          {yamlText}
        </pre>
      </div>
    </div>
  );
}

function EvidencePreview({ content }: { content: PanelContent }) {
  const { t } = useI18n();
  const { title, data } = content;
  const items = (data as Array<{ label: string; value: string }>) || [];
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <FileText size={14} className="text-ldvh-text-secondary" />
        <h4 className="ldvh-card-title">{title || t('objectDetail.closureEvidence')}</h4>
      </div>
      {items.length === 0 ? (
        <p className="ldvh-caption">{t('readingPanel.noEvidence')}</p>
      ) : (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="rounded-md bg-ldvh-bg p-3">
              <p className="ldvh-caption-strong mb-1">{item.label}</p>
              <p className="ldvh-meta-primary whitespace-pre-wrap">{item.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DiffPreview({ content }: { content: PanelContent }) {
  const { t } = useI18n();
  const { title, data } = content;
  const diffText = typeof data === 'string' ? data : '';
  const lines = diffText.split('\n');
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <FileDiff size={14} className="text-ldvh-text-secondary" />
        <h4 className="ldvh-card-title">{title || t('readingPanel.changeDetail')}</h4>
      </div>
      <div className="rounded-md bg-ldvh-bg p-3">
        <pre className="ldvh-meta-primary max-h-[600px] overflow-y-auto whitespace-pre-wrap">
          {lines.map((line, i) => {
            let cls = 'text-ldvh-text-primary';
            if (line.startsWith('+')) cls = 'text-emerald-400';
            else if (line.startsWith('-')) cls = 'text-red-400';
            else if (line.startsWith('@@')) cls = 'text-ldvh-accent';
            return <div key={i} className={cls}>{line}</div>;
          })}
        </pre>
      </div>
    </div>
  );
}
