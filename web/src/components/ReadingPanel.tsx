import { useEffect, useRef, useState, useCallback, type ReactNode } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, X, GripVertical, FileText, ExternalLink } from 'lucide-react';
import { usePanel, type PanelContent } from '@/utils/panelContext';
import MarkdownPreview from '@/components/MarkdownPreview';
import { useI18n } from '@/i18n/context';
import {
  ContentField,
  AdrReadingLayout,
  SparkReadingLayout,
  ObjectIdentityHeader,
  PitfallReadingLayout,
  RelatedContentSection,
  StudyReadingLayout,
  WorkCaseReadingLayout,
  getAuxiliaryMetaEntries,
  getObjectDetailContentEntries,
  splitRelatedContentEntries,
} from '@/pages/ObjectDetail';
import { getObjectStatusLocale } from '@/i18n/locales';
import { fetchDocContent, fetchObjectDetail, fetchObjects, type CommitDetailPanelData, type DocContent, type ObjectDetail as ApiObjectDetail, type ObjectItem } from '@/utils/api';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { getCommitScopeLabel, getCommitTypeLabel } from '@/utils/commitLabels';
import { formatDateTime } from '@/utils/dateFormat';

const MIN_WIDTH = 280;
const MAX_WIDTH_RATIO = 0.58;
const DEFAULT_WIDTH = 380;
const DEFAULT_DOC_WIDTH = 680;
const SNAP_THRESHOLD = 40;
const MOBILE_BREAKPOINT = 768;

const OBJECT_TYPE_LABELS: Record<string, { zh: string; en: string }> = {
  workcase: { zh: '工作', en: 'WorkCase' },
  adr: { zh: '决策', en: 'ADR' },
  pitfall: { zh: '经验', en: 'Pitfall' },
  spark: { zh: '火花', en: 'Spark' },
  study: { zh: '外部调研', en: 'External study' },
  change: { zh: '提交', en: 'Commit' },
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
    if (!isMobile && (content?.type === 'doc' || content?.type === 'web')) {
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
          <div className="z-10 flex shrink-0 items-center justify-between gap-2 border-b border-ldvh-border bg-ldvh-panel/95 px-4 py-2 backdrop-blur">
            <div className="flex min-w-0 flex-1 items-center gap-2">
              {navigationControls}
              <div
                className="flex min-h-7 min-w-0 flex-1 cursor-ns-resize items-center justify-center"
                onMouseDown={onSheetHandleDown}
                onTouchStart={onSheetHandleDown}
                aria-label={panelTitle}
              >
                <div className="h-1 w-10 rounded-full bg-ldvh-border" />
              </div>
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
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
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
      className={`relative flex h-full flex-shrink-0 flex-col border-l border-ldvh-border bg-ldvh-panel transition-[width,opacity] duration-200 ease-in-out ${
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
      <div className="z-10 flex shrink-0 items-center justify-between gap-2 border-b border-ldvh-border bg-ldvh-panel/95 px-4 py-3 backdrop-blur">
        <div className="flex min-w-0 items-center gap-2">
          <GripVertical size={14} className="flex-shrink-0 text-ldvh-text-secondary" />
          {navigationControls}
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
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
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
    case 'web': return <WebPreview content={content} />;
    case 'yaml': return <YamlPreview content={content} />;
    case 'evidence': return <EvidencePreview content={content} />;
    case 'diff': return <DiffPreview content={content} />;
    default:
      return (
        <EmptyPanelPreview />
      );
  }
}

function WebPreview({ content }: { content: PanelContent }) {
  const { locale } = useI18n();
  const { url } = content;
  if (!url) return <EmptyPanelPreview />;
  const openLabel = locale === 'en' ? 'New Tab' : '新标签';

  return (
    <div className="flex h-full min-h-[520px] flex-col gap-3">
      <div className="flex min-w-0 items-center justify-between gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel px-3 py-2">
        <span className="ldvh-meta-primary min-w-0 flex-1 truncate">{url}</span>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="ldvh-chip inline-flex shrink-0 items-center gap-1 rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1 text-ldvh-text-primary hover:border-ldvh-accent hover:text-ldvh-accent"
        >
          <ExternalLink size={12} />
          <span>{openLabel}</span>
        </a>
      </div>
      <iframe
        title={url}
        src={url}
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
        referrerPolicy="no-referrer"
        className="min-h-0 flex-1 rounded-lg border border-ldvh-border bg-white"
      />
    </div>
  );
}

function ObjectPreview({ content }: { content: PanelContent }) {
  const { objectType, objectId, data } = content;
  const { locale, t } = useI18n();
  const [detail, setDetail] = useState<ApiObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const obj = (data as Record<string, unknown> | undefined) ?? detail?.data;
  const status = detail?.summary.status ?? (obj?.status as string | undefined);
  const headerStatus = isObjectDetailLayoutType(objectType) ? undefined : status;
  const title = getObjectTitle(obj, objectId, locale);
  const targetPath = String(obj?.path || detail?.target || objectId || '');
  const loading = !obj && !error && Boolean(objectType && objectId);
  const typeColor = objectType ? (CATEGORY_COLORS[objectType] || CATEGORY_COLORS.other) : CATEGORY_COLORS.other;

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
      <ObjectIdentityHeader
        objectType={objectType || ''}
        id={objectId || ''}
        title={title}
        target={targetPath}
        typeColor={typeColor}
        typeLabel={getObjectTypeLabel(objectType, locale)}
        status={headerStatus}
        statusLabel={headerStatus ? getObjectStatusLocale(objectType || '', headerStatus, locale) : undefined}
        source={obj || {}}
        locale={locale}
        created={formatDateTime(obj?.created as string | undefined)}
        updated={formatDateTime(obj?.updated as string | undefined)}
        closedAt={obj?.closed_at ? formatDateTime(obj.closed_at as string) : undefined}
        auxiliaryMetaEntries={obj ? getAuxiliaryMetaEntries(obj, objectType || '') : []}
        copyLabel={t('common.copyObjectPath')}
        copiedLabel={t('common.copiedObjectPath')}
        compact
      />
      {obj && isObjectDetailLayoutType(objectType) && (
        <ObjectSemanticPreview
          objectType={objectType}
          obj={obj}
          objectId={objectId}
          objectPath={typeof obj.path === 'string' ? obj.path : targetPath}
        />
      )}
      {obj && !isObjectDetailLayoutType(objectType) && (
        <GenericObjectPreview
          objectType={objectType}
          obj={obj}
          objectPath={typeof obj.path === 'string' ? obj.path : targetPath}
        />
      )}
    </div>
  );
}

function ObjectSemanticPreview({
  objectType,
  obj,
  objectId,
  objectPath,
}: {
  objectType?: string;
  obj: Record<string, unknown>;
  objectId?: string;
  objectPath?: string;
}) {
  const [summary, setSummary] = useState<ObjectItem | null>(null);
  const [loading, setLoading] = useState(false);
  const { locale, getStatus } = useI18n();

  useEffect(() => {
    if (!objectType || !objectId) return;
    if (!isObjectDetailLayoutType(objectType)) return;
    if (objectType === 'pitfall' || objectType === 'adr' || objectType === 'spark' || objectType === 'study') {
      setSummary(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setSummary(null);

    fetchObjects('workcase')
      .then((result) => {
        if (cancelled) return;
        const items = result.data?.items ?? [];
        setSummary(items.find((plan) => plan.id === objectId) ?? null);
      })
      .catch(() => {
        if (!cancelled) setSummary(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [objectType, objectId]);

  if (objectType === 'workcase') {
    return <WorkCaseReadingLayout obj={obj} summary={summary} loading={loading} locale={locale} getStatus={getStatus} />;
  }
  if (objectType === 'pitfall') {
    const entries = getObjectDetailContentEntries(obj, objectType);
    const { relatedEntries } = splitRelatedContentEntries(entries);
    return <PitfallReadingLayout obj={obj} relatedEntries={relatedEntries} locale={locale} />;
  }
  if (objectType === 'adr') {
    const entries = getObjectDetailContentEntries(obj, objectType);
    const { relatedEntries } = splitRelatedContentEntries(entries);
    return <AdrReadingLayout obj={obj} relatedEntries={relatedEntries} locale={locale} />;
  }
  if (objectType === 'spark') {
    const entries = getObjectDetailContentEntries(obj, objectType);
    const { relatedEntries } = splitRelatedContentEntries(entries);
    return <SparkReadingLayout obj={obj} relatedEntries={relatedEntries} locale={locale} />;
  }
  if (objectType === 'study') {
    const entries = getObjectDetailContentEntries(obj, objectType);
    const { primaryEntries, relatedEntries } = splitRelatedContentEntries(entries);
    return (
      <StudyReadingLayout
        obj={obj}
        extraEntries={primaryEntries}
        relatedEntries={relatedEntries}
        locale={locale}
        objectPath={objectPath}
      />
    );
  }
  return null;
}

function isObjectDetailLayoutType(objectType: string | undefined) {
  return objectType === 'workcase' || objectType === 'pitfall' || objectType === 'adr' || objectType === 'spark' || objectType === 'study';
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

function GenericObjectPreview({ objectType, obj, objectPath }: { objectType?: string; obj: Record<string, unknown>; objectPath?: string }) {
  const { locale } = useI18n();
  const entries = getObjectDetailContentEntries(obj, objectType || '');
  const { primaryEntries, relatedEntries } = splitRelatedContentEntries(entries);
  if (entries.length === 0) return null;

  return (
    <div className="mb-6 flex flex-col gap-5">
      {primaryEntries.map(([fieldKey, value]) => (
        <ContentField key={fieldKey} fieldKey={fieldKey} value={value} locale={locale} objType={objectType || ''} objectPath={objectPath} />
      ))}
      <RelatedContentSection entries={relatedEntries} locale={locale} />
    </div>
  );
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

interface CommitStatFile {
  path: string;
  stat: string;
  additions: number;
  deletions: number;
}

interface ParsedCommitStat {
  commit?: string;
  author?: string;
  date?: string;
  files: CommitStatFile[];
  summary?: {
    filesChanged?: number;
    insertions?: number;
    deletions?: number;
    raw: string;
  };
}

function isCommitDetailPanelData(value: unknown): value is CommitDetailPanelData {
  return Boolean(
    value
      && typeof value === 'object'
      && 'entry' in value
      && 'stat' in value
      && typeof (value as { stat?: unknown }).stat === 'string',
  );
}

function parseCommitStat(stat: string): ParsedCommitStat {
  const parsed: ParsedCommitStat = { files: [] };
  const lines = stat.split('\n');

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (!line) return;

    if (line.startsWith('commit ')) {
      parsed.commit = line.replace(/^commit\s+/, '').slice(0, 12);
      return;
    }
    if (line.startsWith('Author:')) {
      parsed.author = line.replace(/^Author:\s*/, '');
      return;
    }
    if (line.startsWith('Date:')) {
      parsed.date = line.replace(/^Date:\s*/, '');
      return;
    }

    const summaryMatch = line.match(/(?:(\d+)\s+files?\s+changed)?(?:,\s*)?(?:(\d+)\s+insertions?\(\+\))?(?:,\s*)?(?:(\d+)\s+deletions?\(-\))?/);
    if (summaryMatch && (summaryMatch[1] || summaryMatch[2] || summaryMatch[3])) {
      parsed.summary = {
        filesChanged: summaryMatch[1] ? Number(summaryMatch[1]) : undefined,
        insertions: summaryMatch[2] ? Number(summaryMatch[2]) : undefined,
        deletions: summaryMatch[3] ? Number(summaryMatch[3]) : undefined,
        raw: line,
      };
      return;
    }

    const separatorIndex = rawLine.lastIndexOf('|');
    if (separatorIndex === -1) return;

    const path = rawLine.slice(0, separatorIndex).trim();
    const fileStat = rawLine.slice(separatorIndex + 1).trim();
    if (!path || !fileStat) return;

    parsed.files.push({
      path,
      stat: fileStat,
      additions: (fileStat.match(/\+/g) || []).length,
      deletions: (fileStat.match(/-/g) || []).length,
    });
  });

  return parsed;
}

function CommitMetric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: 'add' | 'delete';
}) {
  const toneClass = tone === 'add'
    ? 'text-emerald-300'
    : tone === 'delete'
      ? 'text-red-300'
      : 'text-ldvh-text-primary';

  return (
    <div className="rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 text-center">
      <div className={`font-mono text-lg font-semibold leading-tight ${toneClass}`}>{value}</div>
      <div className="ldvh-caption mt-0.5">{label}</div>
    </div>
  );
}

function getCommitNodeNextState(state: 'collapsed' | 'expanded') {
  return state === 'collapsed' ? 'expanded' : 'collapsed';
}

function CommitReadingNodeSection({
  title,
  state,
  locale,
  onToggle,
  children,
}: {
  title: string;
  state: 'collapsed' | 'expanded';
  locale: string;
  onToggle: () => void;
  children: ReactNode;
}) {
  const StateIcon = state === 'collapsed' ? ChevronDown : ChevronUp;
  const nextState = getCommitNodeNextState(state);
  const action = locale === 'en'
    ? (nextState === 'collapsed' ? 'Collapse' : 'Expand')
    : (nextState === 'collapsed' ? '收拢' : '展开');

  return (
    <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
      <button
        type="button"
        onClick={onToggle}
        aria-label={locale === 'en' ? `${action} ${title}` : `${action}${title}`}
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

const COMMIT_BODY_SECTION_TITLES = new Set([
  '关键变更',
  '动机',
  '验证结论',
  '影响边界',
  '风险与后续',
]);

function formatCommitBodyForReading(value: string) {
  return value
    .trim()
    .split('\n')
    .map((line) => {
      const match = line.match(/^([^\S\r\n]*)([^:：\n]+)\s*[:：]\s*$/);
      if (!match) return line;
      const [, indent, rawTitle] = match;
      const title = rawTitle.trim();
      if (indent || !COMMIT_BODY_SECTION_TITLES.has(title)) return line;
      return `### ${title}`;
    })
    .join('\n');
}

type CommitBodySection = {
  key: string;
  title: string;
  content: string;
};

function getCommitBodySectionsForReading(value: string, fallbackTitle: string): CommitBodySection[] {
  const formatted = formatCommitBodyForReading(value);
  const sections: CommitBodySection[] = [];
  let currentTitle = fallbackTitle;
  let current: string[] = [];

  formatted.split('\n').forEach((line) => {
    const headingMatch = line.match(/^###\s+(.+?)\s*$/);
    if (headingMatch) {
      if (current.some((item) => item.trim())) {
        sections.push({
          key: `${sections.length}:${currentTitle}`,
          title: currentTitle,
          content: current.join('\n').trim(),
        });
      }
      currentTitle = headingMatch[1].trim();
      current = [];
      return;
    }
    current.push(line);
  });

  if (current.some((line) => line.trim())) {
    sections.push({
      key: `${sections.length}:${currentTitle}`,
      title: currentTitle,
      content: current.join('\n').trim(),
    });
  }

  return sections.length > 0
    ? sections
    : formatted
      ? [{ key: 'commit-body', title: fallbackTitle, content: formatted }]
      : [];
}

function CommitIdentitySection({
  entry,
  parsed,
  title,
  labels,
  locale,
}: {
  entry?: CommitDetailPanelData['entry'];
  parsed: ParsedCommitStat;
  title: string;
  labels: {
    category: string;
    type: string;
    scope: string;
    commit: string;
    time: string;
    copyHash: string;
    copiedHash: string;
  };
  locale: string;
}) {
  const commitColor = CATEGORY_COLORS.other;
  const commitValue = entry?.shortHash || parsed.commit || '—';
  const copyValue = entry?.hash || commitValue;
  const timeValue = entry?.date ? formatDateTime(entry.date) : parsed.date || '—';
  const typeLabel = locale === 'en' ? 'Commit' : labels.commit;
  const headerMetaItems = [
    entry?.category ? getCommitTypeLabel(entry.category, locale) : '',
    entry?.scope ? getCommitScopeLabel(entry.scope, locale) : '',
  ].filter(Boolean);

  return (
    <ObjectIdentityHeader
      title={title}
      id={headerMetaItems.join(' · ')}
      target={copyValue}
      objectType="changelog"
      typeColor={commitColor}
      typeLabel={typeLabel}
      source={{}}
      locale={locale}
      created=""
      updated=""
      showDefaultDates={false}
      titleMetaEntries={[{ label: labels.time, value: timeValue }]}
      titleMetaAlign="footerEnd"
      copyLabel={labels.copyHash}
      copiedLabel={labels.copiedHash}
      extraBadges={(
        <>
        {entry?.isBreaking && (
          <span className="ldvh-chip shrink-0 rounded bg-red-500/10 px-2 py-0.5 text-red-300">
            !
          </span>
        )}
        </>
      )}
    />
  );
}

type CommitDetailLabels = {
  category: string;
  type: string;
  scope: string;
  commit: string;
  time: string;
  summary: string;
  files: string;
  insertions: string;
  deletions: string;
  commitBody: string;
  changedFiles: string;
  noFiles: string;
  raw: string;
  copyHash: string;
  copiedHash: string;
};

function getCommitDetailLabels(locale: string): CommitDetailLabels {
  return locale === 'en'
    ? {
      category: 'Category',
      type: 'Type',
      scope: 'Scope',
      commit: 'Commit',
      time: 'Commit',
      summary: 'Change summary',
      files: 'Files',
      insertions: 'Insertions',
      deletions: 'Deletions',
      commitBody: 'Commit notes',
      changedFiles: 'Changed files',
      noFiles: 'No file stat available',
      raw: 'Original info',
      copyHash: 'Copy commit hash',
      copiedHash: 'Commit hash copied',
    }
    : {
      category: '分类',
      type: '类型',
      scope: '范围',
      commit: '提交',
      time: '提交',
      summary: '变更统计',
      files: '文件',
      insertions: '新增',
      deletions: '删除',
      commitBody: '关键变更',
      changedFiles: '改动文件',
      noFiles: '没有可展示的文件统计',
      raw: '原始信息',
      copyHash: '复制提交 hash',
      copiedHash: '已复制提交 hash',
    };
}

export function CommitDetailIdentity({
  entry,
  stat,
  title,
}: {
  entry?: CommitDetailPanelData['entry'];
  stat: string;
  title?: string;
}) {
  const { locale, t } = useI18n();
  const parsed = parseCommitStat(stat);
  const displayTitle = entry?.description || entry?.message || title || t('readingPanel.changeDetail');
  const labels = getCommitDetailLabels(locale);

  return (
    <CommitIdentitySection
      entry={entry}
      parsed={parsed}
      title={displayTitle}
      labels={labels}
      locale={locale}
    />
  );
}

export function CommitDetailContent({
  entry,
  stat,
  title,
  showIdentity = true,
}: {
  entry?: CommitDetailPanelData['entry'];
  stat: string;
  title?: string;
  showIdentity?: boolean;
}) {
  const { locale, t } = useI18n();
  const [bodySectionStates, setBodySectionStates] = useState<Record<string, 'collapsed' | 'expanded'>>({});
  const [filesState, setFilesState] = useState<'collapsed' | 'expanded'>('collapsed');
  const [rawState, setRawState] = useState<'collapsed' | 'expanded'>('collapsed');
  const diffText = stat;
  const commitBody = entry?.body?.trim() ?? '';
  const parsed = parseCommitStat(diffText);
  const displayTitle = entry?.description || entry?.message || title || t('readingPanel.changeDetail');
  const labels = getCommitDetailLabels(locale);
  const summary = parsed.summary;
  const filesChanged = summary?.filesChanged ?? parsed.files.length;
  const insertions = summary?.insertions ?? parsed.files.reduce((total, file) => total + file.additions, 0);
  const deletions = summary?.deletions ?? parsed.files.reduce((total, file) => total + file.deletions, 0);
  const lines = diffText.split('\n');
  const commitBodySections = commitBody ? getCommitBodySectionsForReading(commitBody, labels.commitBody) : [];

  useEffect(() => {
    setBodySectionStates({});
  }, [entry?.hash, commitBody]);

  return (
    <div className="mb-6 flex flex-col gap-5">
      {showIdentity && (
        <CommitIdentitySection
          entry={entry}
          parsed={parsed}
          title={displayTitle}
          labels={labels}
          locale={locale}
        />
      )}

      <section className="rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
        <div className="ldvh-section-title mb-3 flex w-full min-w-0 items-center gap-2 text-left">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-accent" />
          <span className="min-w-0 flex-1 truncate">{labels.summary}</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <CommitMetric label={labels.files} value={filesChanged} />
          <CommitMetric label={labels.insertions} value={insertions} tone="add" />
          <CommitMetric label={labels.deletions} value={deletions} tone="delete" />
        </div>
      </section>

      {commitBody && commitBodySections.map((section) => {
        const sectionState = bodySectionStates[section.key] ?? 'expanded';
        return (
          <CommitReadingNodeSection
            key={section.key}
            title={section.title}
            state={sectionState}
            locale={locale}
            onToggle={() => {
              setBodySectionStates((current) => ({
                ...current,
                [section.key]: getCommitNodeNextState(sectionState),
              }));
            }}
          >
            <div className="ldvh-study-node-content">
              <MarkdownPreview
                content={section.content}
                className="ldvh-inline-markdown ldvh-commit-body-markdown max-w-none"
              />
            </div>
          </CommitReadingNodeSection>
        );
      })}

      <CommitReadingNodeSection
        title={labels.changedFiles}
        state={filesState}
        locale={locale}
        onToggle={() => setFilesState((current) => getCommitNodeNextState(current))}
      >
        {parsed.files.length === 0 ? (
          <p className="ldvh-body-muted">{labels.noFiles}</p>
        ) : (
          <div className="divide-y divide-ldvh-border/70 rounded-lg border border-ldvh-border bg-ldvh-bg/40">
            {parsed.files.map((file) => (
              <div key={`${file.path}:${file.stat}`} className="px-3 py-2">
                <div className="ldvh-meta-primary break-all font-mono">{file.path}</div>
                <div className="ldvh-caption mt-1 font-mono text-ldvh-text-secondary">{file.stat}</div>
              </div>
            ))}
          </div>
        )}
      </CommitReadingNodeSection>

      <CommitReadingNodeSection
        title={labels.raw}
        state={rawState}
        locale={locale}
        onToggle={() => setRawState((current) => getCommitNodeNextState(current))}
      >
        {diffText ? (
          <pre className="ldvh-meta-primary max-h-[360px] overflow-y-auto whitespace-pre-wrap rounded-lg border border-ldvh-border bg-ldvh-bg/40 px-3 py-2">
            {lines.map((line, i) => {
              let cls = 'text-ldvh-text-primary';
              if (line.startsWith('+')) cls = 'text-emerald-400';
              else if (line.startsWith('-')) cls = 'text-red-400';
              else if (line.startsWith('@@')) cls = 'text-ldvh-accent';
              return <div key={i} className={cls}>{line}</div>;
            })}
          </pre>
        ) : (
          <p className="ldvh-body-muted">{labels.noFiles}</p>
        )}
      </CommitReadingNodeSection>
      </div>
  );
}

function DiffPreview({ content }: { content: PanelContent }) {
  const { title, data } = content;
  const commitData = isCommitDetailPanelData(data) ? data : null;

  return (
    <CommitDetailContent
      entry={commitData?.entry}
      stat={commitData?.stat ?? (typeof data === 'string' ? data : '')}
      title={title}
    />
  );
}
