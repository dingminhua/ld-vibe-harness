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
      <h1 className="ldvh-page-title">{title}</h1>
      {subtitle && <p className="ldvh-page-subtitle mt-1">{subtitle}</p>}
      {children && <div className="mt-3">{children}</div>}
    </div>
  );
}
