import { ReactNode, useState, useEffect, useCallback } from 'react';
import Sidebar from './Sidebar';
import ReadingPanel from './ReadingPanel';
import { PanelProvider, usePanel } from '@/utils/panelContext';

const SIDEBAR_STORAGE_KEY = 'ldvh-sidebar-collapsed';

interface LayoutProps {
  children: ReactNode;
}

/** Inner layout that consumes panel context */
function LayoutInner({ children }: LayoutProps) {
  const { isOpen: panelOpen, closePanel } = usePanel();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });

  // Listen for Escape to close right panel
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && panelOpen) {
        closePanel();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [panelOpen, closePanel]);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
      } catch (error) {
        void error;
      }
      return next;
    });
  }, []);

  return (
    <div className="flex h-screen min-w-[375px] overflow-hidden bg-ldvh-bg">
      {/* 左侧导航 — 可折叠 */}
      <div className="flex-shrink-0">
        <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      </div>

      {/* 中间主内容 */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* 右侧扩展阅读区 */}
      <ReadingPanel />
    </div>
  );
}

export default function Layout({ children }: LayoutProps) {
  return (
    <PanelProvider>
      <LayoutInner>{children}</LayoutInner>
    </PanelProvider>
  );
}
