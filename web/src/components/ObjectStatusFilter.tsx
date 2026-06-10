import { useEffect, useMemo, useState } from 'react';
import { fetchObjects, type ObjectItem } from '@/utils/api';
import { useI18n } from '@/i18n/context';

interface StatusOption {
  status: string;
  count: number;
}

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
  return Array.from(counts, ([status, count]) => ({ status, count }));
}

function getButtonClass(active: boolean): string {
  return `ldvh-chip rounded-full px-3 py-1 transition-colors ${
    active
      ? 'bg-ldvh-accent/15 text-ldvh-accent'
      : 'bg-ldvh-border/50 text-ldvh-text-secondary hover:text-ldvh-text-primary'
  }`;
}

export default function ObjectStatusFilter({
  type,
  activeStatus,
  onChange,
  className = '',
}: ObjectStatusFilterProps) {
  const [items, setItems] = useState<ObjectItem[]>([]);
  const { t, getStatus } = useI18n();

  useEffect(() => {
    let cancelled = false;
    fetchObjects(type)
      .then((result) => {
        if (!cancelled) setItems(result.data?.items ?? []);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      });
    return () => {
      cancelled = true;
    };
  }, [type]);

  const options = useMemo(() => getStatusOptions(items), [items]);
  const total = items.length;

  if (options.length <= 1) return null;

  return (
    <div className={`flex flex-wrap gap-1.5 ${className}`} aria-label={t('objectList.statusFilter')}>
      <button
        type="button"
        onClick={() => onChange(null)}
        className={getButtonClass(activeStatus === null)}
      >
        {t('objectList.all')}
        <span className="ml-1 opacity-70">{total}</span>
      </button>
      {options.map((option) => (
        <button
          key={option.status}
          type="button"
          onClick={() => onChange(option.status)}
          className={getButtonClass(activeStatus === option.status)}
        >
          {getStatus(option.status)}
          <span className="ml-1 opacity-70">{option.count}</span>
        </button>
      ))}
    </div>
  );
}
