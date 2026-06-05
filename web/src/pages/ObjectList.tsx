import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import StatusBadge from '@/components/StatusBadge';
import { fetchObjects, type ObjectItem } from '@/utils/api';
import { useI18n } from '@/i18n/context';

function getLocalizedTitle(item: ObjectItem, locale: string): string {
  if (locale === 'en') {
    return item.title_en || item.title || item.id;
  }
  return item.title_zh || item.title || item.id;
}

export default function ObjectList() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStatus, setActiveStatus] = useState<string | null>(null);
  const { t, getStatus, locale } = useI18n();

  const currentType = type ?? 'task';

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchObjects(currentType, activeStatus ?? undefined)
      .then((result) => {
        setItems(result.data?.items ?? []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [currentType, activeStatus]);

  const allStatuses = Array.from(new Set(items.map((o) => o.status)));

  return (
    <div className="p-6">
      {/* Status filter pills */}
      {allStatuses.length > 1 && (
        <div className="mb-4 flex flex-wrap gap-1.5">
          <button
            onClick={() => setActiveStatus(null)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              activeStatus === null
                ? 'bg-ldvh-accent/15 text-ldvh-accent'
                : 'bg-ldvh-border/50 text-ldvh-text-secondary hover:text-ldvh-text-primary'
            }`}
          >
            {t('objectList.all')}
          </button>
          {allStatuses.map((status) => (
            <button
              key={status}
              onClick={() => setActiveStatus(status)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                activeStatus === status
                  ? 'bg-ldvh-accent/15 text-ldvh-accent'
                  : 'bg-ldvh-border/50 text-ldvh-text-secondary hover:text-ldvh-text-primary'
              }`}
            >
              {getStatus(status)}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
        </div>
      ) : error ? (
        <div className="py-20 text-center text-ldvh-text-secondary">
          <p>{t('common.loadFailed')}</p>
          <p className="font-mono text-xs text-red-400">{error}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="py-20 text-center text-ldvh-text-secondary">
          {t('objectList.noObjects', { type: currentType })}
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((obj) => (
            <button
              key={obj.id}
              onClick={() => navigate(`/objects/${currentType}/${obj.id}`)}
              className="group flex flex-col gap-2 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left transition-colors hover:border-ldvh-accent/40"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-mono text-xs text-ldvh-text-secondary">{obj.id}</span>
                <StatusBadge status={obj.status} statusLabel={getStatus(obj.status)} />
              </div>
              <span className="text-sm text-ldvh-text-primary group-hover:text-ldvh-accent transition-colors">
                {getLocalizedTitle(obj, locale)}
              </span>
              <span className="font-mono text-xs text-ldvh-text-secondary">
                {obj.updated}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
