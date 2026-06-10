import { useEffect, useRef, useState, useCallback } from 'react';
import { X, GripVertical, FileText, FileDiff } from 'lucide-react';
import { usePanel, type PanelContent } from '@/utils/panelContext';

const MIN_WIDTH = 280;
const MAX_WIDTH_RATIO = 0.50;
const DEFAULT_WIDTH = 380;
const SNAP_THRESHOLD = 40;
const MOBILE_BREAKPOINT = 768;

export default function ReadingPanel() {
  const { isOpen, content, closePanel } = usePanel();
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
      const newMax = Math.floor(window.innerWidth * MAX_WIDTH_RATIO);
      setWidth(prev => clamp(prev));
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
            <h3 className="truncate text-sm font-medium text-ldvh-text-primary">
              {content?.title || '扩展阅读'}
            </h3>
            <button onClick={closePanel} className="rounded p-1 text-ldvh-text-secondary hover:bg-ldvh-border/30">
              <X size={14} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {content && <PanelContentRenderer content={content} />}
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
          <h3 className="truncate text-sm font-medium text-ldvh-text-primary">
            {content?.title || '扩展阅读'}
          </h3>
        </div>
        <button onClick={closePanel} className="rounded p-1 text-ldvh-text-secondary hover:bg-ldvh-border/30">
          <X size={14} />
        </button>
      </div>
      <div className="h-[calc(100%-49px)] overflow-y-auto p-4">
        {content && <PanelContentRenderer content={content} />}
      </div>
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
  const obj = data as Record<string, unknown> | undefined;
  const status = obj?.status as string | undefined;
  const title = (obj?.title as string) || (obj?.title_en as string) || (obj?.title_zh as string) || objectId || '—';
  const description: string | undefined = typeof obj?.description === 'string' ? obj.description : undefined;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <span className="rounded bg-ldvh-accent/20 px-2 py-0.5 text-xs font-medium text-ldvh-accent">{objectType}</span>
        {status && <span className="rounded bg-ldvh-border/30 px-2 py-0.5 text-xs text-ldvh-text-secondary">{status}</span>}
      </div>
      <h3 className="text-base font-semibold text-ldvh-text-primary">{title}</h3>
      {objectId && <p className="font-mono text-xs text-ldvh-text-secondary">{objectId}</p>}
      {description && (
        <p className="text-sm leading-relaxed text-ldvh-text-secondary whitespace-pre-wrap">
          {description.length > 500 ? description.slice(0, 500) + '...' : description}
        </p>
      )}
      {obj?.related_tasks && Array.isArray(obj.related_tasks) && obj.related_tasks.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-ldvh-text-secondary">关联任务</p>
          <div className="flex flex-wrap gap-1">
            {(obj.related_tasks as string[]).map(t => (
              <span key={t} className="rounded bg-ldvh-bg px-2 py-0.5 font-mono text-xs text-ldvh-text-primary">{t}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DocPreview({ content }: { content: PanelContent }) {
  const { docPath, data } = content;
  const docContent = typeof data === 'string' ? data : '';
  return (
    <div className="space-y-3">
      {docPath && <p className="font-mono text-xs text-ldvh-text-secondary break-all">{docPath}</p>}
      <div className="rounded-md bg-ldvh-bg p-3">
        <pre className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-ldvh-text-primary">
          {docContent ? (docContent.length > 2000 ? docContent.slice(0, 2000) + '\n\n... (内容已截断)' : docContent) : '加载中...'}
        </pre>
      </div>
    </div>
  );
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
