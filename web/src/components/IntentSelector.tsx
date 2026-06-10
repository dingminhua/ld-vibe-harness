import { useEffect, useState, useRef } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { fetchObjects, type ObjectItem } from '@/utils/api';
import { useI18n } from '@/i18n/context';

interface IntentSelectorProps {
  currentIntentId: string;
  onSelect: (intentId: string) => void;
  onClose: () => void;
}

export default function IntentSelector({ currentIntentId, onSelect, onClose }: IntentSelectorProps) {
  const { locale, t } = useI18n();
  const [intents, setIntents] = useState<ObjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchObjects('intent')
      .then((result) => {
        const items = result.data.items.filter(
          (item) => item.status === 'active' || item.status === 'draft'
        );
        setIntents(items);
      })
      .catch(() => setIntents([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const filtered = search
    ? intents.filter((item) => {
        const q = search.toLowerCase();
        return (
          item.id.toLowerCase().includes(q) ||
          (item.title || '').toLowerCase().includes(q) ||
          (item.title_en || '').toLowerCase().includes(q) ||
          (item.title_zh || '').toLowerCase().includes(q)
        );
      })
    : intents;

  return (
    <div
      ref={containerRef}
      className="absolute left-0 top-full z-50 mt-1 w-80 rounded-lg border border-ldvh-border bg-ldvh-panel shadow-xl"
    >
      {/* Search input */}
      <div className="border-b border-ldvh-border p-2">
        <div className="flex items-center gap-2 rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1.5">
          <Search size={13} className="shrink-0 text-ldvh-text-secondary" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={locale === 'en' ? 'Search intents...' : '搜索意图...'}
            className="ldvh-caption w-full bg-transparent text-ldvh-text-primary outline-none placeholder:text-ldvh-text-secondary"
            autoFocus
          />
        </div>
      </div>

      {/* Intent list */}
      <div className="max-h-60 overflow-y-auto p-1">
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 size={16} className="animate-spin text-ldvh-text-secondary" />
            <span className="ldvh-caption ml-2">{t('common.loading')}</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="ldvh-caption py-4 text-center">
            {locale === 'en' ? 'No intents found' : '未找到意图'}
          </div>
        ) : (
          filtered.map((item) => {
            const displayTitle = locale === 'en'
              ? (item.title_en || item.title)
              : (item.title_zh || item.title);
            const isCurrent = item.id === currentIntentId;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (!isCurrent) onSelect(item.id);
                  else onClose();
                }}
                disabled={isCurrent}
                className={`ldvh-body flex w-full items-center gap-2 rounded-md px-3 py-2 text-left transition-colors ${
                  isCurrent
                    ? 'bg-ldvh-accent/10 text-ldvh-accent cursor-default'
                    : 'text-ldvh-text-primary hover:bg-ldvh-border/30'
                }`}
              >
                <span className="ldvh-meta shrink-0 text-ldvh-accent">{item.id}</span>
                <span className="min-w-0 flex-1 truncate">{displayTitle || item.id}</span>
                {isCurrent && (
                  <span className="ldvh-caption shrink-0">
                    {locale === 'en' ? 'Current' : '当前'}
                  </span>
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
