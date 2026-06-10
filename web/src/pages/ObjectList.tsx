import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t, getStatus, locale } = useI18n();

  const currentType = type ?? 'task';
  const activeStatus = searchParams.get('status');

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

  const handleStatusChange = (status: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    if (status) {
      nextParams.set('status', status);
    } else {
      nextParams.delete('status');
    }
    setSearchParams(nextParams);
  };

  const detailSearch = searchParams.toString();

  return (
    <div className="p-6">
      <ObjectStatusFilter
        type={currentType}
        activeStatus={activeStatus}
        onChange={handleStatusChange}
        className="mb-4"
      />

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
        </div>
      ) : error ? (
        <div className="py-20 text-center text-ldvh-text-secondary">
          <p>{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
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
              onClick={() => navigate(`/objects/${currentType}/${obj.id}${detailSearch ? `?${detailSearch}` : ''}`)}
              className="group flex flex-col gap-2 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left transition-colors hover:border-ldvh-accent/40"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="ldvh-meta">{obj.id}</span>
                <StatusBadge status={obj.status} statusLabel={getStatus(obj.status)} />
              </div>
              <span className="ldvh-card-title transition-colors group-hover:text-ldvh-accent">
                {getLocalizedTitle(obj, locale)}
              </span>
              <span className="ldvh-meta">
                {obj.updated}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
