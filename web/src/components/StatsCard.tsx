import { useTheme } from '@/hooks/useTheme';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { getStatusColor } from '@/utils/statusColors';

interface StatsCardProps {
  type: string;
  label?: string;
  count: number;
  byStatus: Record<string, number>;
  getStatus?: (status: string) => string;
  onClick?: () => void;
}

export default function StatsCard({ type, label, count, byStatus, getStatus, onClick }: StatsCardProps) {
  const { resolved } = useTheme();
  const total = count;
  const entries = Object.entries(byStatus);

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
        <span className="font-mono text-xl font-semibold text-ldvh-accent">{total}</span>
      </div>
      {/* Status distribution bar */}
      {entries.length > 0 && (
        <div key={resolved} className="flex h-1.5 w-full overflow-hidden rounded-full bg-ldvh-border/50">
          {entries.map(([status, statusCount]) => (
            <div
              key={status}
              className="h-full"
              style={{
                width: `${(statusCount / total) * 100}%`,
                backgroundColor: getStatusColor(status),
              }}
              title={`${getStatus ? getStatus(status) : status}: ${statusCount}`}
            />
          ))}
        </div>
      )}
      {/* Status labels */}
      {entries.length > 0 && (
        <div key={`labels-${resolved}`} className="flex flex-wrap gap-1">
          {entries.map(([status, statusCount]) => (
            <span
              key={status}
              className="ldvh-meta"
              style={{ color: getStatusColor(status) }}
            >
              {getStatus ? getStatus(status) : status} {statusCount}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
