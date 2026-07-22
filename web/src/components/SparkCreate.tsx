import { useEffect, useState, type FormEvent } from 'react';
import { createPortal } from 'react-dom';
import { Plus, X, Loader2 } from 'lucide-react';
import { useI18n } from '@/i18n/context';

const API_BASE = '/api';

interface SparkCreateProps {
  onCreated?: () => void;
}

export default function SparkCreate({ onCreated }: SparkCreateProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [intent, setIntent] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('P3');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const { t } = useI18n();

  const reset = () => {
    setTitle('');
    setIntent('');
    setDescription('');
    setPriority('P3');
    setError(null);
    setSuccess(false);
  };

  // Esc 关闭弹窗
  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { setIsOpen(false); reset(); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch(`${API_BASE}/sparks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, intent, description, priority }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.errors?.join(', ') || err?.error || `HTTP ${res.status}`);
      }

      setSuccess(true);
      onCreated?.();
      setTimeout(() => {
        setIsOpen(false);
        reset();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('spark.createFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="ldvh-chip inline-flex items-center gap-1.5 rounded-md border border-dashed border-ldvh-border px-3 py-1.5 text-ldvh-text-secondary transition-colors hover:border-ldvh-accent/40 hover:text-ldvh-accent"
        title={t('spark.create')}
      >
        <Plus size={14} />
        {t('spark.quickCapture')}
      </button>
    );
  }

  // 用 Portal 挂到 body，避免被父级 sticky/transform 容器限制 fixed 定位
  return createPortal(
    <div className="fixed inset-0 z-[100]">
      {/* 遮罩：fixed 全屏，点击关闭 */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={() => { setIsOpen(false); reset(); }}
      />
      {/* 面板定位层：不拦截遮罩点击 */}
      <div className="pointer-events-none absolute inset-0 flex items-start justify-center pt-[10vh]">
        <div className="pointer-events-auto relative w-full max-w-lg rounded-lg border border-ldvh-border bg-ldvh-panel shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between gap-2 border-b border-ldvh-border px-4 py-3">
          <h2 className="ldvh-section-title">{t('spark.create')}</h2>
          <button
            onClick={() => { setIsOpen(false); reset(); }}
            className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30 hover:text-ldvh-text-primary"
          >
            <X size={14} />
          </button>
        </div>

        {/* Form */}
        {success ? (
          <div className="flex flex-col items-center justify-center py-10">
            <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
            <p className="ldvh-body text-emerald-400">{t('spark.created')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 p-4">
            <div>
              <label className="ldvh-caption-strong mb-1 block">{t('spark.title')}</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                required
                placeholder={t('spark.titlePlaceholder')}
                className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 placeholder:text-ldvh-text-secondary focus:border-ldvh-accent/40 focus:outline-none"
              />
            </div>

            <div>
              <label className="ldvh-caption-strong mb-1 block">{t('spark.intent')}</label>
              <textarea
                value={intent}
                onChange={e => setIntent(e.target.value)}
                required
                rows={3}
                placeholder={t('spark.intentPlaceholder')}
                aria-describedby="spark-intent-help"
                className="ldvh-body w-full resize-y rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 placeholder:text-ldvh-text-secondary focus:border-ldvh-accent/40 focus:outline-none"
              />
              <p id="spark-intent-help" className="ldvh-meta-muted mt-1.5">
                {t('spark.intentHelp')}
              </p>
            </div>

            <div>
              <label className="ldvh-caption-strong mb-1 block">{t('spark.description')}</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                required
                rows={8}
                placeholder={t('spark.descriptionPlaceholder')}
                aria-describedby="spark-description-help"
                className="ldvh-body w-full resize-y rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 placeholder:text-ldvh-text-secondary focus:border-ldvh-accent/40 focus:outline-none"
              />
              <p id="spark-description-help" className="ldvh-meta-muted mt-1.5">
                {t('spark.descriptionHelp')}
              </p>
            </div>

            <div>
                <label className="ldvh-caption-strong mb-1 block">{t('spark.priority')}</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 focus:border-ldvh-accent/40 focus:outline-none"
                >
                  <option value="P0">P0</option>
                  <option value="P1">P1</option>
                  <option value="P2">P2</option>
                  <option value="P3">P3</option>
                </select>
            </div>

            {error && (
              <div className="rounded-md bg-red-500/10 px-3 py-2">
                <p className="ldvh-caption text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="ldvh-card-title w-full rounded-md bg-ldvh-accent px-4 py-2 text-white transition-colors hover:bg-ldvh-accent/80 disabled:opacity-50"
            >
              {submitting ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin" />
                  {t('spark.creating')}
                </span>
              ) : (
                t('spark.createBtn')
              )}
            </button>
          </form>
        )}
        </div>
      </div>
    </div>,
    document.body
  );
}
