import { useState, type ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';

interface ContentCardProps {
  title?: string;
  icon?: ReactNode;
  headerExtra?: ReactNode;
  collapsible?: boolean;
  defaultOpen?: boolean;
  children: ReactNode;
}

export default function ContentCard({ title, icon, headerExtra, collapsible = false, defaultOpen = true, children }: ContentCardProps) {
  const [open, setOpen] = useState(defaultOpen);

  const showHeader = title || icon || headerExtra || collapsible;

  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-panel">
      {showHeader && (
        <div className="flex items-center justify-between gap-2 border-b border-ldvh-border px-4 py-3">
          <div className="flex min-w-0 items-center gap-2">
            {icon && <span className="flex-shrink-0 text-ldvh-text-secondary">{icon}</span>}
            {title && (
              <h3 className="truncate text-sm font-semibold text-ldvh-text-primary">{title}</h3>
            )}
          </div>
          <div className="flex flex-shrink-0 items-center gap-2">
            {headerExtra}
            {collapsible && (
              <button
                onClick={() => setOpen(!open)}
                className="rounded p-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/30"
              >
                <ChevronDown size={14} className={`transition-transform ${open ? '' : '-rotate-90'}`} />
              </button>
            )}
          </div>
        </div>
      )}
      {(!collapsible || open) && (
        <div className="p-4">{children}</div>
      )}
    </div>
  );
}
