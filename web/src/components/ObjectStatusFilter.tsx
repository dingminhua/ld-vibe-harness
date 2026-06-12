import { useEffect, useMemo, useState } from 'react';
import { fetchObjects, type ObjectItem } from '@/utils/api';
import { useI18n } from '@/i18n/context';

interface StatusOption {
  status: string;
  count: number;
}

const STATUS_FILTER_ORDER = [
  'active',
  'executing',
  'review_needed',
  'verifying',
  'planned',
  'draft',
  'proposed',
  'accepted',
  'closed',
  'resolved',
  'archived',
  'superseded',
  'rejected',
  'deprecated',
  'suspended',
];

const statusOrderIndex = new Map(STATUS_FILTER_ORDER.map((status, index) => [status, index]));

const FALLBACK_STATUSES_BY_TYPE: Record<string, string[]> = {
  workarea: ['active', 'archived'],
  taskplan: ['active', 'review_needed', 'closed'],
  task: ['executing', 'planned', 'review_needed', 'closed'],
  subtask: ['planned', 'review_needed', 'closed'],
  adr: ['proposed', 'accepted', 'rejected'],
  pitfall: ['active', 'superseded'],
  memo: ['active', 'draft'],
};

interface ObjectStatusFilterProps {
  type: string;
  activeStatus: string | null;
  onChange: (status: string | null) => void;
  className?: string;
}

function getStatusOptions(items: ObjectItem[]): StatusOption[] {
  const counts = new Map<string, number>();
  for (const item of items) {
    if (!item.status) continue;
    counts.set(item.status, (counts.get(item.status) ?? 0) + 1);
  }
  return Array.from(counts, ([status, count]) => ({ status, count })).sort((a, b) => {
    const aIndex = statusOrderIndex.get(a.status) ?? Number.MAX_SAFE_INTEGER;
    const bIndex = statusOrderIndex.get(b.status) ?? Number.MAX_SAFE_INTEGER;
    if (aIndex !== bIndex) return aIndex - bIndex;
    if (a.count !== b.count) return b.count - a.count;
    return a.status.localeCompare(b.status);
  });
}

function getButtonClass(active: boolean): string {
  return `ldvh-chip rounded-full px-3 py-1 transition-colors ${
    active
      ? 'bg-ldvh-accent/15 text-ldvh-accent'
      : 'bg-ldvh-border/50 text-ldvh-text-secondary hover:text-ldvh-text-primary'
  }`;
}

function getFallbackStatuses(type: string, activeStatus: string | null): string[] {
  const fallback = FALLBACK_STATUSES_BY_TYPE[type] ?? [];
  if (!activeStatus || fallback.includes(activeStatus)) return fallback;
  return [activeStatus, ...fallback];
}

function CountPlaceholder() {
  return (
    <span aria-hidden="true" className="ml-1 inline-flex min-w-4 items-center justify-center gap-0.5 align-middle">
      <span className="h-1 w-1 animate-pulse rounded-full bg-current opacity-35" />
      <span className="h-1 w-1 animate-pulse rounded-full bg-current opacity-35 [animation-delay:150ms]" />
      <span className="h-1 w-1 animate-pulse rounded-full bg-current opacity-35 [animation-delay:300ms]" />
    </span>
  );
}

export default function ObjectStatusFilter({
  type,
  activeStatus,
  onChange,
  className = '',
}: ObjectStatusFilterProps) {
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { t, getStatus } = useI18n();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchObjects(type)
      .then((result) => {
        if (!cancelled) setItems(result.data?.items ?? []);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [type]);

  const options = useMemo(() => getStatusOptions(items), [items]);
  const fallbackStatuses = useMemo(() => getFallbackStatuses(type, activeStatus), [type, activeStatus]);
  const total = items.length;

  if (loading && options.length === 0) {
    return (
      <div className={`flex min-h-7 flex-wrap gap-1.5 ${className}`} aria-label={t('objectList.statusFilter')} aria-busy="true">
        {fallbackStatuses.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => onChange(status)}
            className={getButtonClass(activeStatus === status)}
          >
            {getStatus(status)}
            <CountPlaceholder />
          </button>
        ))}
        <button
          type="button"
          onClick={() => onChange(null)}
          className={getButtonClass(activeStatus === null)}
        >
          {t('objectList.all')}
          <CountPlaceholder />
        </button>
      </div>
    );
  }

  if (options.length <= 1) return null;

  return (
    <div className={`flex min-h-7 flex-wrap gap-1.5 ${className}`} aria-label={t('objectList.statusFilter')}>
      {options.map((option) => (
        <button
          key={option.status}
          type="button"
          onClick={() => onChange(option.status)}
          className={getButtonClass(activeStatus === option.status)}
        >
          {getStatus(option.status)}
          <span className="ml-1 inline-block min-w-4 text-center opacity-70">{option.count}</span>
        </button>
      ))}
      <button
        type="button"
        onClick={() => onChange(null)}
        className={getButtonClass(activeStatus === null)}
      >
        {t('objectList.all')}
        <span className="ml-1 inline-block min-w-4 text-center opacity-70">{total}</span>
      </button>
    </div>
  );
}
