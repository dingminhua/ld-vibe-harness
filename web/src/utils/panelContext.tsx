import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

export type PanelContentType = 'object' | 'doc' | 'yaml' | 'evidence' | 'diff' | 'empty';

export interface PanelContent {
  type: PanelContentType;
  title?: string;
  objectType?: string;
  objectId?: string;
  docPath?: string;
  data?: unknown;
}

interface PanelContextValue {
  isOpen: boolean;
  content: PanelContent | null;
  openPanel: (content: PanelContent) => void;
  closePanel: () => void;
  togglePanel: () => void;
}

const PanelContext = createContext<PanelContextValue>({
  isOpen: false,
  content: null,
  openPanel: () => {},
  closePanel: () => {},
  togglePanel: () => {},
});

export function PanelProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState<PanelContent | null>(null);

  const openPanel = useCallback((c: PanelContent) => {
    setContent(c);
    setIsOpen(true);
  }, []);

  const closePanel = useCallback(() => {
    setIsOpen(false);
    setTimeout(() => { setContent(null); }, 200);
  }, []);

  const togglePanel = useCallback(() => {
    setIsOpen((prev) => {
      if (prev && !content) return false;
      return !prev;
    });
  }, [content]);

  return (
    <PanelContext.Provider value={{ isOpen, content, openPanel, closePanel, togglePanel }}>
      {children}
    </PanelContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePanel() {
  return useContext(PanelContext);
}
