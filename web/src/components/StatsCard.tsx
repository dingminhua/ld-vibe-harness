import { useTheme } from '@/hooks/useTheme';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { getStatusColor } from '@/utils/statusColors';
import { useI18n } from '@/i18n/context';
import type { FactCoverageStatus } from '@/utils/api';

interface StatsCardProps {
  type: string;
  label?: string;
  count: number;
  distribution: Record<string, number>;
  getStatus?: (status: string) => string;
  onClick?: () => void;
  coverageStatus?: FactCoverageStatus;
}

export default function StatsCard({ type, label, count, distribution, getStatus, onClick, coverageStatus = 'complete' }: StatsCardProps) {
  const { resolved } = useTheme();
  const { t } = useI18n();
  const total = count;
  const entries = Object.entries(distribution);

  return (
    <button
      onClick={onClick}
      className="group flex flex-col gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left transition-colors hover:border-ldvh-accent/40"
    >
      <div className="flex items-center justify-between">
        <span className="ldvh-card-title flex min-w-0 items-center gap-2">
          <ObjectTypeIcon type={type} size={14} className="shrink-0 text-ldvh-accent" />
          <span className="min-w-0 truncate">{label ?? type}</span>
        </span>
        <span className="font-mono text-xl font-semibold text-ldvh-accent">
          {coverageStatus === 'unavailable' ? '—' : coverageStatus === 'partial' ? `${total}+` : total}
        </span>
      </div>
      {coverageStatus !== 'complete' && (
        <p className={`ldvh-meta ${coverageStatus === 'partial' ? 'text-amber-400' : 'text-red-400'}`}>
          {coverageStatus === 'partial'
            ? t('dashboard.coveragePartial')
            : t('dashboard.coverageUnavailable')}
        </p>
      )}
      {/* Current-state distribution bar */}
      {coverageStatus !== 'unavailable' && total > 0 && entries.length > 0 && (
        <div key={resolved} className="flex h-1.5 w-full overflow-hidden rounded-full bg-ldvh-border/50">
          {entries.map(([state, stateCount]) => (
            <div
              key={state}
              className="h-full"
              style={{
                width: `${(stateCount / total) * 100}%`,
                backgroundColor: getStatusColor(state),
              }}
              title={`${getStatus ? getStatus(state) : state}: ${stateCount}`}
            />
          ))}
        </div>
      )}
      {/* Current-state labels */}
      {coverageStatus !== 'unavailable' && entries.length > 0 && (
        <div key={`labels-${resolved}`} className="flex flex-wrap gap-1">
          {entries.map(([state, stateCount]) => (
            <span
              key={state}
              className="ldvh-meta"
              style={{ color: getStatusColor(state) }}
            >
              {getStatus ? getStatus(state) : state} {stateCount}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
