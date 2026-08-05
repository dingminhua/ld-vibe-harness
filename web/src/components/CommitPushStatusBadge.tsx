import { ArrowUp, GitCommitHorizontal } from 'lucide-react';
import { useState } from 'react';
import { useI18n } from '@/i18n/context';
import type { GitPushStatus } from '@/utils/api';

export default function CommitPushStatusBadge({
  status,
  className = '',
}: {
  status: GitPushStatus;
  className?: string;
}) {
  const { t } = useI18n();
  const [showTooltip, setShowTooltip] = useState(false);

  if (status === 'unknown') return null;

  const isPushed = status === 'pushed';
  const label = t(isPushed ? 'changelog.pushed' : 'changelog.unpushed');

  // A commit already reachable from the upstream does not need a per-row
  // decoration. Only surface the actionable local-ahead state.
  if (isPushed) return null;

  return (
    <span className={`${className} relative inline-flex shrink-0`}>
      <span
        aria-label={label}
        className="inline-flex h-6 w-6 items-center justify-center rounded-md text-rose-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/45 dark:text-rose-400"
        onBlur={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        role="img"
        tabIndex={0}
      >
        <span className="relative block h-4 w-4" aria-hidden="true">
          <GitCommitHorizontal className="absolute inset-0" size={16} strokeWidth={2} />
          <ArrowUp
            className="absolute -right-1 -top-1 bg-ldvh-panel"
            size={10}
            strokeWidth={3}
          />
        </span>
      </span>
      {showTooltip ? (
        <span
          className="pointer-events-none absolute right-0 top-full z-20 mt-1 whitespace-nowrap rounded-md border border-ldvh-border bg-ldvh-panel px-2 py-1 text-[10px] font-medium leading-4 text-ldvh-text-primary shadow-md"
          role="tooltip"
        >
          {label}
        </span>
      ) : null}
    </span>
  );
}
