import { useEffect, useRef, useState, useCallback } from 'react';
import { ChevronLeft, ChevronRight, X, GripVertical, FileText, FileDiff } from 'lucide-react';
import { usePanel, type PanelContent } from '@/utils/panelContext';
import ChecklistCard from '@/components/ChecklistCard';
import DocPreviewLink from '@/components/DocPreviewLink';
import EvidenceBlock from '@/components/EvidenceBlock';
import MarkdownPreview from '@/components/MarkdownPreview';
import ReferenceCard from '@/components/ReferenceCard';
import StatusBadge from '@/components/StatusBadge';
import { useI18n } from '@/i18n/context';
import { fetchDocContent, fetchObjectDetail, type DocContent, type ObjectDetail as ApiObjectDetail } from '@/utils/api';

const MIN_WIDTH = 280;
const MAX_WIDTH_RATIO = 0.50;
const DEFAULT_WIDTH = 380;
const DEFAULT_DOC_WIDTH = 520;
const SNAP_THRESHOLD = 40;
const MOBILE_BREAKPOINT = 768;

export default function ReadingPanel() {
  const { isOpen, content, canGoBack, canGoForward, goBack, goForward, closePanel } = usePanel();
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
      setWidth(prev => Math.min(prev, Math.floor(window.innerWidth * 0.50)));
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

  const panelTitle = content?.title || '扩展阅读';
  const preview = content ? <PanelContentRenderer content={content} /> : <EmptyPanelPreview />;
  const navigationControls = (
    <div className="flex shrink-0 items-center gap-1">
      <button
        type="button"
        onClick={goBack}
        disabled={!canGoBack}
        className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary disabled:cursor-default disabled:opacity-35"
        title="上一个访问对象"
        aria-label="上一个访问对象"
      >
        <ChevronLeft size={14} />
      </button>
      <button
        type="button"
        onClick={goForward}
        disabled={!canGoForward}
        className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary disabled:cursor-default disabled:opacity-35"
        title="下一个访问对象"
        aria-label="下一个访问对象"
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
              <h3 className="truncate text-sm font-medium text-ldvh-text-primary">{panelTitle}</h3>
            </div>
            <button onClick={closePanel} className="rounded p-1 text-ldvh-text-secondary hover:bg-ldvh-border/30">
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
          <h3 className="truncate text-sm font-medium text-ldvh-text-primary">{panelTitle}</h3>
        </div>
        <button onClick={closePanel} className="rounded p-1 text-ldvh-text-secondary hover:bg-ldvh-border/30">
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
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <p className="text-sm text-ldvh-text-secondary">选择一个对象或文档以在此预览</p>
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
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-sm text-ldvh-text-secondary">选择一个对象或文档以在此预览</p>
        </div>
      );
  }
}

function ObjectPreview({ content }: { content: PanelContent }) {
  const { objectType, objectId, data } = content;
  const { locale, getStatus } = useI18n();
  const [detail, setDetail] = useState<ApiObjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const obj = (data as Record<string, unknown> | undefined) ?? detail?.data;
  const status = detail?.summary.status ?? (obj?.status as string | undefined);
  const title = getObjectTitle(obj, objectId, locale);
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
        <p className="text-sm text-red-300">加载失败</p>
        <p className="mt-1 font-mono text-xs text-red-300/80">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="rounded bg-ldvh-accent/20 px-2 py-0.5 text-xs font-medium text-ldvh-accent">{objectType}</span>
        {status && <StatusBadge status={status} statusLabel={getStatus(status)} size="sm" />}
      </div>
      <h3 className="text-base font-semibold text-ldvh-text-primary">{title}</h3>
      {objectId && <p className="font-mono text-xs text-ldvh-text-secondary">{objectId}</p>}
      {objectType === 'task' && obj ? (
        <TaskObjectPreview obj={obj} />
      ) : (
        <GenericObjectPreview obj={obj} />
      )}
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

function TaskObjectPreview({ obj }: { obj: Record<string, unknown> }) {
  return (
    <div className="space-y-4">
      <PreviewSection title="任务目标">
        {typeof obj.description === 'string' && obj.description ? (
          <PreviewText value={obj.description} />
        ) : (
          <EmptyPreview text="未记录任务描述" />
        )}
        {typeof obj.source_intent === 'string' && obj.source_intent && (
          <div className="mt-3">
            <PreviewLabel>来源意图</PreviewLabel>
            <ReferenceCard refs={[obj.source_intent]} />
          </div>
        )}
      </PreviewSection>

      {typeof obj.acceptance === 'string' && obj.acceptance && (
        <PreviewSection title="验收标准">
          <ChecklistCard value={obj.acceptance} />
        </PreviewSection>
      )}

      {typeof obj.verification === 'string' && obj.verification && (
        <PreviewSection title="验证方式">
          <EvidenceBlock value={obj.verification} embedded />
        </PreviewSection>
      )}

      {typeof obj.closure_evidence === 'string' && obj.closure_evidence && (
        <PreviewSection title="关闭证据">
          <EvidenceBlock value={obj.closure_evidence} embedded />
        </PreviewSection>
      )}

      <PreviewDocGroup title="产出物" docs={obj.deliverables} />
      <PreviewDocGroup title="关联文档" docs={obj.related_docs} />

      {Array.isArray(obj.blocked_by) && obj.blocked_by.length > 0 && (
        <PreviewSection title="前置依赖">
          <ReferenceCard refs={obj.blocked_by as string[]} />
        </PreviewSection>
      )}
    </div>
  );
}

function GenericObjectPreview({ obj }: { obj: Record<string, unknown> | undefined }) {
  if (!obj) return null;
  return (
    <div className="space-y-4">
      {typeof obj.description === 'string' && obj.description && <PreviewText value={obj.description} />}
      {Array.isArray(obj.related_tasks) && obj.related_tasks.length > 0 && (
        <PreviewSection title="关联任务">
          <ReferenceCard refs={obj.related_tasks as string[]} />
        </PreviewSection>
      )}
    </div>
  );
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
  return <p className="text-xs font-medium text-ldvh-text-secondary">{children}</p>;
}

function PreviewText({ value }: { value: string }) {
  return (
    <p className="whitespace-pre-wrap text-sm leading-relaxed text-ldvh-text-secondary">
      {value}
    </p>
  );
}

function EmptyPreview({ text }: { text: string }) {
  return <span className="text-sm italic text-ldvh-text-secondary">{text}</span>;
}

function PreviewDocGroup({ title, docs }: { title: string; docs: unknown }) {
  if (!Array.isArray(docs) || docs.length === 0) return null;
  return (
    <PreviewSection title={title}>
      <DocPreviewLink docs={docs as string[]} />
    </PreviewSection>
  );
}

function DocPreview({ content }: { content: PanelContent }) {
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
        {docPath && <p className="break-all font-mono text-xs text-ldvh-text-secondary">{docPath}</p>}
        <div className="rounded-md border border-red-500/20 bg-red-500/10 p-3">
          <p className="text-sm text-red-300">文档加载失败</p>
          <p className="mt-1 font-mono text-xs text-red-300/80">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {docPath && (
        <div>
          <h3 className="truncate text-sm font-semibold text-ldvh-text-primary">{getPathTitle(docPath)}</h3>
          <p className="mt-1 break-all font-mono text-xs text-ldvh-text-secondary">{docPath}</p>
        </div>
      )}
      {!docContent ? (
        <div className="flex items-center justify-center rounded-md bg-ldvh-bg py-16">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
        </div>
      ) : isMarkdown ? (
        <div className="rounded-md bg-ldvh-bg p-4">
          <MarkdownPreview content={docContent} />
          {truncated && <p className="mt-3 text-xs text-ldvh-text-secondary">内容已截断</p>}
        </div>
      ) : (
        <div className="rounded-md bg-ldvh-bg p-3">
          <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-ldvh-text-primary">
            {docContent}
          </pre>
          {truncated && <p className="mt-3 text-xs text-ldvh-text-secondary">内容已截断</p>}
        </div>
      )}
    </div>
  );
}

function getPathTitle(path: string) {
  const parts = path.split('/');
  return parts[parts.length - 1] || path;
}

function YamlPreview({ content }: { content: PanelContent }) {
  const { data } = content;
  const yamlText = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
  return (
    <div className="space-y-3">
      <div className="rounded-md bg-ldvh-bg p-3">
        <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-ldvh-text-primary max-h-[600px] overflow-y-auto">
          {yamlText}
        </pre>
      </div>
    </div>
  );
}

function EvidencePreview({ content }: { content: PanelContent }) {
  const { title, data } = content;
  const items = (data as Array<{ label: string; value: string }>) || [];
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <FileText size={14} className="text-ldvh-text-secondary" />
        <h4 className="text-sm font-medium text-ldvh-text-primary">{title || '关闭证据'}</h4>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-ldvh-text-secondary">暂无证据信息</p>
      ) : (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div key={i} className="rounded-md bg-ldvh-bg p-3">
              <p className="mb-1 text-xs font-medium text-ldvh-text-secondary">{item.label}</p>
              <p className="font-mono text-xs leading-relaxed text-ldvh-text-primary whitespace-pre-wrap">{item.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DiffPreview({ content }: { content: PanelContent }) {
  const { title, data } = content;
  const diffText = typeof data === 'string' ? data : '';
  const lines = diffText.split('\n');
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <FileDiff size={14} className="text-ldvh-text-secondary" />
        <h4 className="text-sm font-medium text-ldvh-text-primary">{title || '变更详情'}</h4>
      </div>
      <div className="rounded-md bg-ldvh-bg p-3">
        <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-ldvh-text-primary max-h-[600px] overflow-y-auto">
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
