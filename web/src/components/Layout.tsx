import { ReactNode, useState, useEffect, useCallback } from 'react';
import { PanelLeft, PanelRight } from 'lucide-react';
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
      try { localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next)); } catch {}
      return next;
    });
  }, []);

  return (
    <div className="flex h-screen min-w-[375px] overflow-hidden bg-ldvh-bg">
      {/* 左侧导航 — 可折叠 */}
      <div
        className={`flex-shrink-0 overflow-hidden transition-[width] duration-200 ease-in-out ${
          sidebarCollapsed ? 'w-0' : 'w-[220px]'
        }`}
      >
        <Sidebar />
      </div>

      {/* 侧栏折叠按钮 */}
      <button
        onClick={toggleSidebar}
        className="absolute left-0 top-1/2 z-20 -translate-y-1/2 translate-x-0 rounded-r-md border border-l-0 border-ldvh-border bg-ldvh-panel p-1.5 text-ldvh-text-secondary transition-all hover:text-ldvh-text-primary"
        style={{ left: sidebarCollapsed ? 0 : 220 }}
        title={sidebarCollapsed ? '展开侧栏' : '收起侧栏'}
      >
        <PanelLeft size={14} className={sidebarCollapsed ? 'rotate-180' : ''} />
      </button>

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
