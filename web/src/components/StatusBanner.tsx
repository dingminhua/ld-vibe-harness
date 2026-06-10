import type { ReactNode } from 'react';
import { ShieldCheck, ShieldAlert, AlertCircle } from 'lucide-react';

interface StatusBannerProps {
  status: 'closed' | 'degraded' | 'open' | 'needs_human_gate';
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  children?: ReactNode;
}

const STATUS_CLASS = {
  closed: 'border-emerald-500/30 bg-emerald-500/10',
  degraded: 'border-yellow-500/30 bg-yellow-500/10',
  open: 'border-red-500/30 bg-red-500/10',
  needs_human_gate: 'border-sky-500/30 bg-sky-500/10',
} as const;

const STATUS_ICON_CLASS = {
  closed: 'text-emerald-400',
  degraded: 'text-yellow-400',
  open: 'text-red-400',
  needs_human_gate: 'text-sky-400',
} as const;

function StatusIcon({ status }: { status: StatusBannerProps['status'] }) {
  const cls = STATUS_ICON_CLASS[status];
  if (status === 'closed') return <ShieldCheck size={20} className={`mt-0.5 flex-shrink-0 ${cls}`} />;
  if (status === 'open') return <ShieldAlert size={20} className={`mt-0.5 flex-shrink-0 ${cls}`} />;
  return <AlertCircle size={20} className={`mt-0.5 flex-shrink-0 ${cls}`} />;
}

export default function StatusBanner({ status, title, description, action, children }: StatusBannerProps) {
  return (
    <div className={`rounded-lg border p-4 ${STATUS_CLASS[status]}`}>
      <div className="flex items-start gap-3">
        <StatusIcon status={status} />
        <div className="min-w-0 flex-1">
          <p className="ldvh-section-title">{title}</p>
          {description && <p className="ldvh-body-muted mt-1">{description}</p>}
          {action && (
            <button
              onClick={action.onClick}
              className="ldvh-chip mt-2 rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-1.5 text-ldvh-text-primary transition-colors hover:bg-ldvh-border/50"
            >
              {action.label}
            </button>
          )}
          {children}
        </div>
      </div>
    </div>
  );
}
