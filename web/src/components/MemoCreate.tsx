import { useState, type FormEvent } from 'react';
import { Plus, X, Loader2 } from 'lucide-react';
import { useI18n } from '@/i18n/context';

const API_BASE = '/api';

interface MemoCreateProps {
  onCreated?: () => void;
}

export default function MemoCreate({ onCreated }: MemoCreateProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [source, setSource] = useState('');
  const [category, setCategory] = useState('discovery');
  const [priority, setPriority] = useState('low');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const { t } = useI18n();

  const reset = () => {
    setTitle('');
    setDescription('');
    setSource('');
    setCategory('discovery');
    setPriority('low');
    setError(null);
    setSuccess(false);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch(`${API_BASE}/memos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, source, category, priority }),
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
      setError(err instanceof Error ? err.message : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="ldvh-chip inline-flex items-center gap-1.5 rounded-md border border-dashed border-ldvh-border px-3 py-1.5 text-ldvh-text-secondary transition-colors hover:border-ldvh-accent/40 hover:text-ldvh-accent"
        title={t('memo.create')}
      >
        <Plus size={14} />
        {t('memo.quickCapture')}
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-[10vh]">
      <div className="w-full max-w-lg rounded-lg border border-ldvh-border bg-ldvh-panel shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between gap-2 border-b border-ldvh-border px-4 py-3">
          <h2 className="ldvh-section-title">{t('memo.create')}</h2>
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
            <p className="ldvh-body text-emerald-400">{t('memo.created')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 p-4">
            <div>
              <label className="ldvh-caption-strong mb-1 block">{t('memo.title')}</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                required
                placeholder={t('memo.titlePlaceholder')}
                className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 placeholder:text-ldvh-text-secondary focus:border-ldvh-accent/40 focus:outline-none"
              />
            </div>

            <div>
              <label className="ldvh-caption-strong mb-1 block">{t('memo.description')}</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                required
                rows={3}
                placeholder={t('memo.descriptionPlaceholder')}
                className="ldvh-body w-full resize-none rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 placeholder:text-ldvh-text-secondary focus:border-ldvh-accent/40 focus:outline-none"
              />
            </div>

            <div>
              <label className="ldvh-caption-strong mb-1 block">{t('memo.source')}</label>
              <input
                type="text"
                value={source}
                onChange={e => setSource(e.target.value)}
                required
                placeholder={t('memo.sourcePlaceholder')}
                className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 placeholder:text-ldvh-text-secondary focus:border-ldvh-accent/40 focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="ldvh-caption-strong mb-1 block">{t('memo.category')}</label>
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 focus:border-ldvh-accent/40 focus:outline-none"
                >
                  <option value="discovery">{t('memo.catDisco')}</option>
                  <option value="reminder">{t('memo.catRemind')}</option>
                  <option value="question">{t('memo.catQuest')}</option>
                  <option value="gap">{t('memo.catGap')}</option>
                  <option value="preference">{t('memo.catPref')}</option>
                </select>
              </div>
              <div>
                <label className="ldvh-caption-strong mb-1 block">{t('memo.priority')}</label>
                <select
                  value={priority}
                  onChange={e => setPriority(e.target.value)}
                  className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2 focus:border-ldvh-accent/40 focus:outline-none"
                >
                  <option value="low">{t('memo.pLow')}</option>
                  <option value="medium">{t('memo.pMed')}</option>
                  <option value="high">{t('memo.pHigh')}</option>
                </select>
              </div>
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
                  {t('memo.creating')}
                </span>
              ) : (
                t('memo.createBtn')
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
