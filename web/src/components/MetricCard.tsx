import type { ReactNode } from 'react';

interface MetricCardProps {
  icon?: ReactNode;
  value: string | number;
  label: string;
  href?: string;
  onClick?: () => void;
  tone?: 'default' | 'green' | 'red';
  size?: 'default' | 'compact';
  detail?: string;
  detailClassName?: string;
}

const TONE_CLASS = {
  default: 'text-ldvh-text-primary',
  green: 'text-emerald-400',
  red: 'text-red-400',
} as const;

export default function MetricCard({ icon, value, label, href, onClick, tone = 'default', size = 'default', detail, detailClassName }: MetricCardProps) {
  const inner = (
    <>
      {icon && <div className="flex-shrink-0 text-ldvh-text-secondary">{icon}</div>}
      <div className="min-w-0">
        <p className={`font-mono font-semibold ${size === 'compact' ? 'text-xl' : 'text-2xl'} ${TONE_CLASS[tone]}`}>
          {value}
        </p>
        <p className="truncate text-xs text-ldvh-text-secondary">{label}</p>
        {detail && <p className={`mt-1 text-xs text-ldvh-text-secondary ${detailClassName || ''}`}>{detail}</p>}
      </div>
    </>
  );

  const className = `flex min-w-0 items-center rounded-lg border border-ldvh-border bg-ldvh-panel transition-colors ${
    size === 'compact' ? 'gap-2 p-3' : 'gap-3 p-4'
  } ${
    onClick || href ? 'cursor-pointer hover:border-ldvh-accent/40' : ''
  }`;

  if (href) {
    return <a href={href} className={`block ${onClick || href ? 'cursor-pointer' : ''}`}><div className={className} onClick={onClick}>{inner}</div></a>;
  }

  return <div className={className} onClick={onClick}>{inner}</div>;
}
