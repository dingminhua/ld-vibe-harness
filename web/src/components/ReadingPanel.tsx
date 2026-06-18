import { useEffect, useRef, useState, useCallback } from 'react';
import { ChevronLeft, ChevronRight, X, GripVertical, FileText, FileDiff, ExternalLink } from 'lucide-react';
import { usePanel, type PanelContent } from '@/utils/panelContext';
import MarkdownPreview from '@/components/MarkdownPreview';
import CopyPathButton from '@/components/CopyPathButton';
import { useI18n } from '@/i18n/context';
import { ContentField, ObjectIdentityHeader, WorkAreaReadingLayout, WorkPlanReadingLayout, getObjectDetailContentEntries } from '@/pages/ObjectDetail';
import { getObjectStatusLocale } from '@/i18n/locales';
import { fetchDocContent, fetchObjectDetail, fetchObjects, type DocContent, type ObjectDetail as ApiObjectDetail, type ObjectItem } from '@/utils/api';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { formatDateTime } from '@/utils/dateFormat';

const MIN_WIDTH = 280;
const MAX_WIDTH_RATIO = 0.58;
const DEFAULT_WIDTH = 380;
const DEFAULT_DOC_WIDTH = 680;
const SNAP_THRESHOLD = 40;
const MOBILE_BREAKPOINT = 768;

const OBJECT_TYPE_LABELS: Record<string, { zh: string; en: string }> = {
  workarea: { zh: '工作域', en: 'Work Area' },
  workplan: { zh: '工作计划', en: 'Work Plan' },
  adr: { zh: '决策', en: 'ADR' },
  pitfall: { zh: '踩坑经验', en: 'Pitfall' },
  memo: { zh: '备忘', en: 'Memo' },
  study: { zh: '研究报告', en: 'Study' },
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
          <div
            className="flex h-10 flex-shrink-0 cursor-ns-resize items-center justify-center border-b border-ldvh-border"
            onMouseDown={onSheetHandleDown}
            onTouchStart={onSheetHandleDown}
          >
            <div className="h-1 w-10 rounded-full bg-ldvh-border" />
          </div>
          <div className="z-10 flex shrink-0 items-center justify-between gap-2 border-b border-ldvh-border bg-ldvh-panel/95 px-4 py-2 backdrop-blur">
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
  const title = getObjectTitle(obj, objectId, locale);
  const targetPath = detail?.target;
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
        status={status}
        statusLabel={status ? getObjectStatusLocale(objectType || '', status, locale) : undefined}
        source={obj || {}}
        locale={locale}
        created={formatDateTime(obj?.created as string | undefined)}
        updated={formatDateTime(obj?.updated as string | undefined)}
        closedAt={obj?.closed_at ? formatDateTime(obj.closed_at as string) : undefined}
        compact
      />
      {obj && isObjectDetailLayoutType(objectType) && <ObjectSemanticPreview objectType={objectType} obj={obj} objectId={objectId} />}
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

function ObjectSemanticPreview({ objectType, obj, objectId }: { objectType?: string; obj: Record<string, unknown>; objectId?: string }) {
  const [summary, setSummary] = useState<ObjectItem | null>(null);
  const [loading, setLoading] = useState(false);
  const { locale, getStatus } = useI18n();

  useEffect(() => {
    if (!objectType || !objectId) return;
    if (!isObjectDetailLayoutType(objectType)) return;
    let cancelled = false;
    setLoading(true);
    setSummary(null);

    const summaryType = objectType === 'workarea' ? 'workarea' : 'workplan';
    fetchObjects(summaryType)
      .then((result) => {
        if (cancelled) return;
        const items = result.data?.items ?? [];
        if (objectType === 'workarea') {
          setSummary(items.find((workarea) => workarea.id === objectId) ?? null);
          return;
        }
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

  if (objectType === 'workarea') {
    return <WorkAreaReadingLayout obj={obj} summary={summary} loading={loading} locale={locale} getStatus={getStatus} />;
  }
  if (objectType === 'workplan') {
    return <WorkPlanReadingLayout obj={obj} summary={summary} loading={loading} locale={locale} getStatus={getStatus} />;
  }
  return null;
}

function isObjectDetailLayoutType(objectType: string | undefined) {
  return objectType === 'workarea' || objectType === 'workplan';
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
  if (entries.length === 0) return null;

  return (
    <div className="mb-6 flex flex-col gap-5">
      {entries.map(([fieldKey, value]) => (
        <ContentField key={fieldKey} fieldKey={fieldKey} value={value} locale={locale} objType={objectType || ''} objectPath={objectPath} />
      ))}
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
