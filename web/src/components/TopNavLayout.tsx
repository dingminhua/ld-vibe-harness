import { ReactNode } from 'react';
import TopNav from './TopNav';

interface LayoutProps {
  children: ReactNode;
}

export default function TopNavLayout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen min-w-[1024px] flex-col overflow-hidden bg-ldvh-bg">
      <TopNav />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
