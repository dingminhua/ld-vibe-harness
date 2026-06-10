import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import CopyPathButton from '@/components/CopyPathButton';
import { fetchObjects, type ObjectItem } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
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
  const openObject = (objId: string) => {
    navigate(`/objects/${currentType}/${objId}${detailSearch ? `?${detailSearch}` : ''}`);
  };

  return (
    <div className="ldvh-page-frame">
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
        <div className="py-20 text-center">
          <p className="ldvh-body-muted">{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t('objectList.noObjects', { type: currentType })}
        </div>
      ) : (
        <div className="ldvh-section-grid">
          {items.map((obj) => (
            <div
              key={obj.id}
              role="button"
              tabIndex={0}
              onClick={() => openObject(obj.id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  openObject(obj.id);
                }
              }}
              className="group flex cursor-pointer flex-col gap-2 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left transition-colors hover:border-ldvh-accent/40"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="ldvh-meta min-w-0 truncate">{obj.id}</span>
                <div className="flex shrink-0 items-center gap-2">
                  <CopyPathButton path={obj.path} />
                  <StatusBadge status={obj.status} statusLabel={getStatus(obj.status)} />
                </div>
              </div>
              <span className="ldvh-card-title transition-colors group-hover:text-ldvh-accent">
                {getLocalizedTitle(obj, locale)}
              </span>
              <span className="ldvh-meta">
                {formatDateTime(obj.updated)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
