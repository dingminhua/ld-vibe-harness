import { useEffect, useState, useCallback } from 'react';
import { X, FileText, Link2, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useI18n } from '@/i18n/context';
import { fetchDocContent, fetchObjectDetail } from '@/utils/api';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import StatusBadge from '@/components/StatusBadge';

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

export type PanelContent =
  | { type: 'doc'; path: string }
  | { type: 'object'; refType: string; refId: string };

interface ReadingPanelProps {
  open: boolean;
  onClose: () => void;
  content: PanelContent | null;
}

export default function ReadingPanel({ open, onClose, content }: ReadingPanelProps) {
  const { t, locale, getStatus } = useI18n();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [docContent, setDocContent] = useState<string | null>(null);
  const [docTruncated, setDocTruncated] = useState(false);
  const [objInfo, setObjInfo] = useState<{
    id: string;
    type: string;
    status: string;
    title: string;
  } | null>(null);

  // Fetch content when panel content changes
  useEffect(() => {
    if (!open || !content) return;

    setLoading(true);
    setError(null);
    setDocContent(null);
    setDocTruncated(false);
    setObjInfo(null);

    if (content.type === 'doc') {
      fetchDocContent(content.path)
        .then((data) => {
          setDocContent(data.content);
          setDocTruncated(data.truncated);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    } else if (content.type === 'object') {
      fetchObjectDetail(content.refType, content.refId)
        .then((detail) => {
          const obj = detail.data;
          const title = (locale === 'en'
            ? (obj.title_en as string || obj.title as string)
            : (obj.title_zh as string || obj.title as string)) || detail.summary.id;
          setObjInfo({
            id: detail.summary.id,
            type: detail.summary.type,
            status: detail.summary.status,
            title,
          });
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }
  }, [open, content, locale]);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  // Mobile drawer drag-to-close
  const [dragStartY, setDragStartY] = useState<number | null>(null);
  const [dragDeltaY, setDragDeltaY] = useState(0);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    setDragStartY(e.touches[0].clientY);
    setDragDeltaY(0);
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (dragStartY === null) return;
    const delta = e.touches[0].clientY - dragStartY;
    setDragDeltaY(Math.max(0, delta));
  }, [dragStartY]);

  const handleTouchEnd = useCallback(() => {
    if (dragDeltaY > 80) {
      onClose();
    }
    setDragStartY(null);
    setDragDeltaY(0);
  }, [dragDeltaY, onClose]);

  // Panel title
  const panelTitle = content
    ? content.type === 'doc'
      ? content.path
      : content.refId
    : '';

  return (
    <>
      {/* Desktop: right side panel */}
      <div
        className={`hidden lg:flex flex-col h-full border-l border-ldvh-border bg-ldvh-panel transition-all duration-300 ease-in-out ${
          open ? 'w-80' : 'w-0'
        } overflow-hidden`}
      >
        {open && (
          <>
            {/* Header */}
            <div className="flex items-center gap-2 border-b border-ldvh-border px-4 py-3">
              {content?.type === 'doc' ? (
                <FileText size={14} className="shrink-0 text-ldvh-accent" />
              ) : (
                <Link2 size={14} className="shrink-0 text-ldvh-accent" />
              )}
              <span className="min-w-0 flex-1 truncate text-xs font-medium text-ldvh-text-secondary">
                {panelTitle}
              </span>
              <button
                onClick={onClose}
                className="shrink-0 rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
              >
                <X size={14} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 size={20} className="animate-spin text-ldvh-accent" />
                  <span className="ml-2 text-sm text-ldvh-text-secondary">{t('common.loading')}</span>
                </div>
              )}
              {error && (
                <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                  <p className="text-sm text-red-400">{t('common.loadFailed')}</p>
                  <p className="mt-1 font-mono text-xs text-red-400/70">{error}</p>
                </div>
              )}
              {content?.type === 'doc' && docContent && (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  {docTruncated && (
                    <p className="text-xs text-ldvh-accent mb-2">{t('readingPanel.truncated')}</p>
                  )}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{docContent}</ReactMarkdown>
                </div>
              )}
              {content?.type === 'object' && objInfo && (
                <ObjectSummaryCard info={objInfo} locale={locale} getStatus={getStatus} />
              )}
            </div>
          </>
        )}
      </div>

      {/* Mobile: bottom drawer */}
      <div
        className={`lg:hidden fixed inset-x-0 bottom-0 z-50 transition-transform duration-300 ease-in-out ${
          open ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ height: '50vh', transform: open ? `translateY(-${dragDeltaY}px)` : undefined }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Backdrop */}
        {open && (
          <div
            className="fixed inset-0 bg-black/40 -z-10"
            onClick={onClose}
          />
        )}

        <div className="flex h-full flex-col rounded-t-xl border-t border-ldvh-border bg-ldvh-panel shadow-lg">
          {/* Drag handle */}
          <div className="flex justify-center py-2">
            <div className="h-1 w-8 rounded-full bg-ldvh-border" />
          </div>

          {/* Header */}
          <div className="flex items-center gap-2 border-b border-ldvh-border px-4 pb-3">
            {content?.type === 'doc' ? (
              <FileText size={14} className="shrink-0 text-ldvh-accent" />
            ) : (
              <Link2 size={14} className="shrink-0 text-ldvh-accent" />
            )}
            <span className="min-w-0 flex-1 truncate text-xs font-medium text-ldvh-text-secondary">
              {panelTitle}
            </span>
            <button
              onClick={onClose}
              className="shrink-0 rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
            >
              <X size={14} />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {loading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="animate-spin text-ldvh-accent" />
                <span className="ml-2 text-sm text-ldvh-text-secondary">{t('common.loading')}</span>
              </div>
            )}
            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                <p className="text-sm text-red-400">{t('common.loadFailed')}</p>
                <p className="mt-1 font-mono text-xs text-red-400/70">{error}</p>
              </div>
            )}
            {content?.type === 'doc' && docContent && (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                {docTruncated && (
                  <p className="text-xs text-ldvh-accent mb-2">{t('readingPanel.truncated')}</p>
                )}
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{docContent}</ReactMarkdown>
              </div>
            )}
            {content?.type === 'object' && objInfo && (
              <ObjectSummaryCard info={objInfo} locale={locale} getStatus={getStatus} />
            )}
          </div>
        </div>
      </div>
    </>
  );
}

/** Object summary card displayed in the reading panel */
function ObjectSummaryCard({
  info,
  locale,
  getStatus,
}: {
  info: { id: string; type: string; status: string; title: string };
  locale: string;
  getStatus: (status: string) => string;
}) {
  const typeColor = CATEGORY_COLORS[info.type] || CATEGORY_COLORS.other;
  const typeLabel = TYPE_LOCALES[info.type]
    ? (locale === 'en' ? TYPE_LOCALES[info.type].en : TYPE_LOCALES[info.type].zh)
    : info.type;

  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-bg p-4">
      <div className="flex items-center gap-2 mb-3">
        <span
          className="rounded px-2 py-0.5 text-xs font-medium"
          style={{ backgroundColor: `${typeColor}20`, color: typeColor }}
        >
          {typeLabel}
        </span>
        <StatusBadge status={info.status} statusLabel={getStatus(info.status)} size="sm" />
      </div>
      <h3 className="text-base font-semibold text-ldvh-text-primary mb-1">{info.title}</h3>
      <p className="font-mono text-xs text-ldvh-text-secondary">{info.id}</p>
    </div>
  );
}
