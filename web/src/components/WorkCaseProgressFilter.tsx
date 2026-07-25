import { useMemo } from 'react';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale } from '@/i18n/locales';
import type { WorkCaseProgressOption } from '@/utils/api';
import {
  WORKCASE_PROGRESS_GROUP_ORDER,
  type WorkCaseProgressGroup,
} from '@/shared/workcaseStatus';

interface WorkCaseProgressFilterProps {
  activeGroup: WorkCaseProgressGroup | null;
  onChange: (group: WorkCaseProgressGroup | null) => void;
  options?: WorkCaseProgressOption[];
  total?: number;
  loading?: boolean;
}

function getButtonClass(active: boolean): string {
  return `ldvh-tab-button ${active ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`;
}

export default function WorkCaseProgressFilter({
  activeGroup,
  onChange,
  options = [],
  total = 0,
  loading = false,
}: WorkCaseProgressFilterProps) {
  const { t, locale } = useI18n();
  const counts = useMemo(() => new Map(options.map((option) => [option.group, option.count])), [options]);

  return (
    <div className="ldvh-tab-list" role="group" aria-label={t('objectList.progressGroupFilter')}>
      {WORKCASE_PROGRESS_GROUP_ORDER.map((group) => (
        <button
          key={group}
          type="button"
          onClick={() => onChange(group)}
          className={getButtonClass(activeGroup === group)}
        >
          {getObjectStatusLocale('workcase', group, locale)}
          <span className="ldvh-tab-count">{loading ? '·' : counts.get(group) ?? 0}</span>
        </button>
      ))}
      <button
        type="button"
        onClick={() => onChange(null)}
        className={getButtonClass(activeGroup === null)}
      >
        {t('objectList.all')}
        <span className="ldvh-tab-count">{loading ? '·' : total}</span>
      </button>
    </div>
  );
}
