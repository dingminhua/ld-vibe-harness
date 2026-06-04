import { useState, useEffect, useCallback } from 'react';

type ThemeMode = 'system' | 'light' | 'dark';
type ResolvedTheme = 'light' | 'dark';

const STORAGE_KEY = 'ldvh-theme-mode';

function getSystemTheme(): ResolvedTheme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveTheme(mode: ThemeMode): ResolvedTheme {
  return mode === 'system' ? getSystemTheme() : mode;
}

export function useTheme() {
  const [mode, setMode] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
    return 'system'; // 默认跟随系统
  });

  const resolved = resolveTheme(mode);

  useEffect(() => {
    const html = document.documentElement;
    html.classList.remove('light', 'dark');
    html.classList.add(resolved);
    html.setAttribute('data-theme', mode);
    localStorage.setItem(STORAGE_KEY, mode);
  }, [mode, resolved]);

  // 监听系统主题变化
  useEffect(() => {
    if (mode !== 'system') return;

    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      // 触发重新渲染以更新 resolved
      setMode('system');
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [mode]);

  const cycleTheme = useCallback(() => {
    setMode(prev => {
      if (prev === 'system') return 'light';
      if (prev === 'light') return 'dark';
      return 'system';
    });
  }, []);

  return {
    mode,
    resolved,
    isDark: resolved === 'dark',
    setMode,
    cycleTheme,
  };
}
