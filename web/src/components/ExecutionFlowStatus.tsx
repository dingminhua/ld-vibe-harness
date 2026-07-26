import type { RelatedObjectSummary } from '@/utils/api';
import {
  EXECUTION_FLOW_ORDER,
  getExecutionFlowCounts,
  getExecutionFlowIcon,
  getExecutionFlowToneLabel,
  executionFlowBarClass,
  executionFlowIconClass,
  executionFlowToneClass,
  type ExecutionFlowTone,
  type ExecutionFlowTranslate,
} from '@/utils/executionFlowStatus';

export function ExecutionFlowBar({
  items,
  t,
  getStatus,
  compact = false,
}: {
  items: RelatedObjectSummary[];
  t: ExecutionFlowTranslate;
  getStatus: (status: string) => string;
  compact?: boolean;
}) {
  const total = items.length;
  const counts = getExecutionFlowCounts(items);
  const entries = EXECUTION_FLOW_ORDER
    .map((tone) => ({
      tone,
      count: counts[tone],
      label: getExecutionFlowToneLabel(tone, t, getStatus),
    }))
    .filter((entry) => entry.count > 0);
  const summary = entries.length > 0
    ? entries.map((entry) => t('objectList.executionFlowCount', { status: entry.label, count: String(entry.count) })).join(' · ')
    : t('objectList.noExecutionItems');
  const heightClass = compact ? 'h-1.5' : 'h-2.5';
  const minWidthClass = compact ? 'min-w-[3px]' : 'min-w-1';

  return (
    <div className="min-w-0" role="group" aria-label={summary} title={summary}>
      <div className={`flex min-w-0 rounded-full bg-ldvh-border/45 ${heightClass}`}>
        {entries.length > 0 ? (
          entries.map((entry, index) => {
            const tooltip = t('objectList.executionFlowCount', { status: entry.label, count: String(entry.count) });
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
                className={`relative h-full outline-none transition-[filter] after:pointer-events-none after:absolute after:bottom-full after:left-1/2 after:z-20 after:mb-1 after:hidden after:-translate-x-1/2 after:whitespace-nowrap after:rounded-md after:border after:border-ldvh-border after:bg-ldvh-panel after:px-2 after:py-1 after:text-xs after:leading-5 after:text-ldvh-text-primary after:shadow-lg after:shadow-black/20 after:content-[attr(data-tooltip)] hover:brightness-110 hover:after:block focus:after:block focus-visible:ring-2 focus-visible:ring-ldvh-accent/70 ${minWidthClass} ${executionFlowBarClass[entry.tone]} ${roundedClass}`}
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

export function ExecutionFlowMarker({
  tone,
  label,
  compact = false,
}: {
  tone: ExecutionFlowTone;
  label: string;
  compact?: boolean;
}) {
  const Icon = getExecutionFlowIcon(tone);
  return (
    <span
      aria-label={label}
      title={label}
      className={`inline-flex shrink-0 items-center justify-center rounded-md border ${compact ? 'h-5 w-5' : 'h-7 w-7'} ${executionFlowToneClass[tone]}`}
    >
      <Icon size={compact ? 11 : 14} strokeWidth={compact ? 2.4 : 2.2} />
    </span>
  );
}
