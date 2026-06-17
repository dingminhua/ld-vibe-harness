import { useMemo } from 'react';
import type { ObjectStatusOption } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale } from '@/i18n/locales';

const STATUS_FILTER_ORDER = [
  'active',
  'executing',
  'review_needed',
  'verifying',
  'planned',
  'pending',
  'draft',
  'proposed',
  'accepted',
  'closed',
  'resolved',
  'discarded',
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
  memo: ['pending', 'resolved', 'discarded'],
  study: ['active', 'draft', 'archived', 'superseded'],
};

interface ObjectStatusFilterProps {
  type: string;
  activeStatus: string | null;
  onChange: (status: string | null) => void;
  options?: ObjectStatusOption[];
  total?: number;
  loading?: boolean;
  className?: string;
}

function sortStatusOptions(options: ObjectStatusOption[]): ObjectStatusOption[] {
  return [...options].sort((a, b) => {
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
  options = [],
  total = 0,
  loading = false,
  className = '',
}: ObjectStatusFilterProps) {
  const { t, locale } = useI18n();

  const sortedOptions = useMemo(() => sortStatusOptions(options), [options]);
  const fallbackStatuses = useMemo(() => getFallbackStatuses(type, activeStatus), [type, activeStatus]);
  const displayOptions = useMemo(() => {
    if (type !== 'memo' && type !== 'study') return sortedOptions;
    const counts = new Map(sortedOptions.map((option) => [option.status, option.count]));
    return fallbackStatuses.map((status) => ({ status, count: counts.get(status) ?? 0 }));
  }, [fallbackStatuses, sortedOptions, type]);

  if (loading && sortedOptions.length === 0) {
    return (
      <div className={`flex min-h-7 flex-wrap gap-1.5 ${className}`} aria-label={t('objectList.statusFilter')} aria-busy="true">
        {fallbackStatuses.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => onChange(status)}
            className={getButtonClass(activeStatus === status)}
          >
            {getObjectStatusLocale(type, status, locale)}
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

  if (displayOptions.length <= 1 && type !== 'memo') return null;

  return (
    <div className={`flex min-h-7 flex-wrap gap-1.5 ${className}`} aria-label={t('objectList.statusFilter')}>
      {displayOptions.map((option) => (
        <button
          key={option.status}
          type="button"
          onClick={() => onChange(option.status)}
          className={getButtonClass(activeStatus === option.status)}
        >
          {getObjectStatusLocale(type, option.status, locale)}
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
