import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}

/** Unified page header for all middle-area pages. */
export default function PageHeader({ title, subtitle, children }: PageHeaderProps) {
  return (
    <div className="mb-6">
      <h1 className="text-xl font-semibold text-ldvh-text-primary">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-ldvh-text-secondary">{subtitle}</p>}
      {children && <div className="mt-3">{children}</div>}
    </div>
  );
}
