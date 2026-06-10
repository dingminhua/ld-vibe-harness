import { useEffect, useRef, useState, useCallback } from 'react';
import { X, GripVertical } from 'lucide-react';
import { usePanel, type PanelContent } from '@/utils/panelContext';

const MIN_WIDTH = 280;
const MAX_WIDTH_RATIO = 0.50; // max 50% of viewport
const DEFAULT_WIDTH = 380;
const SNAP_THRESHOLD = 40; // snap to min/max within this px

export default function ReadingPanel() {
  const { isOpen, content, closePanel } = usePanel();
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isDragging, setIsDragging] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(DEFAULT_WIDTH);

  const maxWidth = Math.floor(window.innerWidth * MAX_WIDTH_RATIO);

  const clamp = useCallback(
    (w: number) => Math.max(MIN_WIDTH, Math.min(w, maxWidth)),
    [maxWidth],
  );

  const onMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);
      startXRef.current = e.clientX;
      startWidthRef.current = width;
    },
    [width],
  );

  useEffect(() => {
    if (!isDragging) return;

    const onMouseMove = (e: MouseEvent) => {
      const dx = startXRef.current - e.clientX;
      let newW = startWidthRef.current + dx;
      // Snap to max width
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

  // Update max width on window resize
  useEffect(() => {
    const onResize = () => {
      const newMax = Math.floor(window.innerWidth * MAX_WIDTH_RATIO);
      setWidth(prev => clamp(prev));
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [clamp]);

  if (!isOpen && !content) return null;

  return (
    <div
      ref={panelRef}
      className={`relative flex-shrink-0 border-l border-ldvh-border bg-ldvh-panel transition-[width,opacity] duration-200 ease-in-out ${
        isOpen ? 'opacity-100' : 'w-0 overflow-hidden opacity-0 border-l-0'
      }`}
      style={{ width: isOpen ? width : 0 }}
    >
      {/* 拖拽手柄 */}
      <div
        className="absolute left-0 top-0 z-10 flex h-full w-2 cursor-col-resize items-center justify-center transition-colors hover:bg-ldvh-accent/20"
        onMouseDown={onMouseDown}
      >
        <div className="flex h-12 w-1.5 flex-col items-center justify-center rounded-full bg-ldvh-border/50 opacity-0 transition-opacity group-hover:opacity-100 hover:opacity-100" />
      </div>

      {/* 头部 */}
      <div className="flex items-center justify-between gap-2 border-b border-ldvh-border px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <GripVertical size={14} className="flex-shrink-0 text-ldvh-text-secondary" />
          <h3 className="truncate text-sm font-medium text-ldvh-text-primary">
            {content?.title || '扩展阅读'}
          </h3>
        </div>
        <div className="flex flex-shrink-0 items-center gap-1">
          <button
            onClick={closePanel}
            className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary"
            title="关闭面板"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* 内容区 */}
      <div className="h-[calc(100%-49px)] overflow-y-auto p-4">
        {content && <PanelContentRenderer content={content} />}
      </div>
    </div>
  );
}

/** 根据内容类型渲染不同视图 */
function PanelContentRenderer({ content }: { content: PanelContent }) {
  switch (content.type) {
    case 'object':
      return <ObjectPreview content={content} />;
    case 'doc':
      return <DocPreview content={content} />;
    case 'yaml':
      return <YamlPreview content={content} />;
    case 'empty':
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
        {status && (
          <span className="rounded bg-ldvh-border/30 px-2 py-0.5 text-xs text-ldvh-text-secondary">{status}</span>
        )}
      </div>
      <h3 className="text-base font-semibold text-ldvh-text-primary">{title}</h3>
      {objectId && <p className="font-mono text-xs text-ldvh-text-secondary">{objectId}</p>}
      {description && (
        <p className="text-sm leading-relaxed text-ldvh-text-secondary whitespace-pre-wrap">
          {(description && description.length > 500) ? description.slice(0, 500) + '...' : description}
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
