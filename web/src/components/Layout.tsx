import { ReactNode, useState, useEffect, useCallback } from 'react';
import Sidebar from './Sidebar';
import ReadingPanel from './ReadingPanel';
import { PanelProvider, usePanel } from '@/utils/panelContext';

const SIDEBAR_STORAGE_KEY = 'ldvh-sidebar-collapsed';
// Default: expanded. Only collapse when user has explicitly chosen to.
const SIDEBAR_DEFAULT_EXPANDED = false;

interface LayoutProps {
  children: ReactNode;
}

/** Inner layout that consumes panel context */
function LayoutInner({ children }: LayoutProps) {
  const { isOpen: panelOpen, closePanel, openPanel } = usePanel();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY);
      if (stored === null) return SIDEBAR_DEFAULT_EXPANDED;
      return localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
    } catch {
      return SIDEBAR_DEFAULT_EXPANDED;
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

  useEffect(() => {
    const onRefPreview = (event: Event) => {
      const { refType, refId, title } = (event as CustomEvent<{ refType?: string; refId?: string; title?: string }>).detail ?? {};
      if (!refType || !refId) return;
      event.preventDefault();
      openPanel({ type: 'object', title: title || refId, objectType: refType, objectId: refId });
    };
    document.addEventListener('ldvh:ref-preview', onRefPreview);
    return () => document.removeEventListener('ldvh:ref-preview', onRefPreview);
  }, [openPanel]);

  useEffect(() => {
    const onDocPreview = (event: Event) => {
      const { path } = (event as CustomEvent<{ path?: string }>).detail ?? {};
      if (!path || path.startsWith('http')) return;
      event.preventDefault();
      openPanel({ type: 'doc', title: path, docPath: path });
    };
    document.addEventListener('ldvh:doc-preview', onDocPreview);
    return () => document.removeEventListener('ldvh:doc-preview', onDocPreview);
  }, [openPanel]);

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
