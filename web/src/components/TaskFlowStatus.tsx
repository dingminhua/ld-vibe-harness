import type { RelatedObjectSummary } from '@/utils/api';
import {
  TASK_FLOW_LEGEND_ORDER,
  TASK_FLOW_ORDER,
  getTaskFlowCounts,
  getTaskFlowIcon,
  getTaskFlowToneLabel,
  taskFlowBarClass,
  taskFlowIconClass,
  taskFlowToneClass,
  type TaskFlowTone,
  type TaskFlowTranslate,
} from '@/utils/taskFlowStatus';

export function TaskFlowBar({
  tasks,
  t,
  getStatus,
  compact = false,
}: {
  tasks: RelatedObjectSummary[];
  t: TaskFlowTranslate;
  getStatus: (status: string) => string;
  compact?: boolean;
}) {
  const total = tasks.length;
  const counts = getTaskFlowCounts(tasks);
  const entries = TASK_FLOW_ORDER
    .map((tone) => ({
      tone,
      count: counts[tone],
      label: getTaskFlowToneLabel(tone, t, getStatus),
    }))
    .filter((entry) => entry.count > 0);
  const summary = entries.length > 0
    ? entries.map((entry) => t('objectList.taskFlowCount', { status: entry.label, count: String(entry.count) })).join(' · ')
    : t('objectList.noTasks');
  const heightClass = compact ? 'h-1.5' : 'h-2.5';
  const minWidthClass = compact ? 'min-w-[3px]' : 'min-w-1';

  return (
    <div className="min-w-0" role="group" aria-label={summary} title={summary}>
      <div className={`flex min-w-0 rounded-full bg-ldvh-border/45 ${heightClass}`}>
        {entries.length > 0 ? (
          entries.map((entry, index) => {
            const tooltip = t('objectList.taskFlowCount', { status: entry.label, count: String(entry.count) });
            const roundedClass = entries.length === 1
              ? 'rounded-full'
              : `${index === 0 ? 'rounded-l-full' : ''} ${index === entries.length - 1 ? 'rounded-r-full' : ''}`;
            return (
              <div
                key={entry.tone}
                tabIndex={0}
                aria-label={tooltip}
                title={tooltip}
                data-tooltip={tooltip}
                className={`relative h-full outline-none transition-[filter] after:pointer-events-none after:absolute after:bottom-full after:left-1/2 after:z-20 after:mb-1 after:hidden after:-translate-x-1/2 after:whitespace-nowrap after:rounded-md after:border after:border-ldvh-border after:bg-ldvh-panel after:px-2 after:py-1 after:text-xs after:leading-5 after:text-ldvh-text-primary after:shadow-lg after:shadow-black/20 after:content-[attr(data-tooltip)] hover:brightness-110 hover:after:block focus:after:block focus-visible:ring-2 focus-visible:ring-ldvh-accent/70 ${minWidthClass} ${taskFlowBarClass[entry.tone]} ${roundedClass}`}
                style={{ width: `${(entry.count / total) * 100}%` }}
              />
            );
          })
        ) : (
          <div className="h-full w-full rounded-full bg-ldvh-border/45" />
        )}
      </div>
    </div>
  );
}

export function TaskFlowLegend({
  t,
  getStatus,
}: {
  t: TaskFlowTranslate;
  getStatus: (status: string) => string;
}) {
  return (
    <div className="flex min-h-7 flex-wrap items-center justify-end gap-x-2.5 gap-y-1" aria-label={t('objectList.taskFlowLegend')}>
      {TASK_FLOW_LEGEND_ORDER.map((tone) => {
        const label = getTaskFlowToneLabel(tone, t, getStatus);
        const Icon = getTaskFlowIcon(tone);
        return (
          <span key={tone} className="ldvh-caption inline-flex items-center gap-1.5 text-ldvh-text-secondary">
            <Icon size={12} strokeWidth={2.2} className={taskFlowIconClass[tone]} />
            <span>{label}</span>
          </span>
        );
      })}
    </div>
  );
}

export function TaskFlowMarker({
  tone,
  label,
  compact = false,
}: {
  tone: TaskFlowTone;
  label: string;
  compact?: boolean;
}) {
  const Icon = getTaskFlowIcon(tone);
  return (
    <span
      aria-label={label}
      title={label}
      className={`inline-flex shrink-0 items-center justify-center rounded-md border ${compact ? 'h-5 w-5' : 'h-7 w-7'} ${taskFlowToneClass[tone]}`}
    >
      <Icon size={compact ? 11 : 14} strokeWidth={compact ? 2.4 : 2.2} />
    </span>
  );
}
