import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Target,
  Lightbulb,
  GitBranch,
  BookOpen,
  Shield,
  Bug,
  StickyNote,
  Globe,
  ClipboardCheck,
  FlaskConical,
  Sun,
  Moon,
  Monitor,
  PanelLeft,
  ShieldCheck,
} from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { useTheme } from '@/hooks/useTheme';
import type { LocaleKey } from '@/i18n/locales';

const NAV_ITEMS: { to: string; labelKey: LocaleKey; icon: typeof LayoutDashboard }[] = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/workbench', labelKey: 'nav.workbench', icon: FlaskConical },
  { to: '/objects/intent', labelKey: 'nav.intents', icon: Lightbulb },
  { to: '/objects/task', labelKey: 'nav.tasks', icon: Target },
  { to: '/objects/adr', labelKey: 'nav.adrs', icon: GitBranch },
  { to: '/objects/pitfall', labelKey: 'nav.pitfalls', icon: Bug },
  { to: '/objects/memo', labelKey: 'nav.memos', icon: StickyNote },
  { to: '/objects/profile', labelKey: 'nav.profiles', icon: BookOpen },
  { to: '/validate', labelKey: 'nav.validate', icon: Shield },
  { to: '/gate', labelKey: 'nav.gate', icon: ShieldCheck },
  { to: '/changelog', labelKey: 'nav.changelog', icon: ClipboardCheck },
];

function ThemeIcon({ mode }: { mode: 'system' | 'light' | 'dark' }) {
  if (mode === 'light') return <Sun size={16} />;
  if (mode === 'dark') return <Moon size={16} />;
  return <Monitor size={16} />;
}

function IconTooltip({ label }: { label: string }) {
  return (
    <span
      aria-hidden="true"
      className="ldvh-chip pointer-events-none absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2 whitespace-nowrap rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1 text-ldvh-text-primary opacity-0 shadow-lg shadow-black/10 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
    >
      {label}
    </span>
  );
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { locale, setLocale, t } = useI18n();
  const { mode, cycleTheme } = useTheme();
  const languageLabel = locale === 'zh' ? t('language.switchToEnglish') : t('language.switchToChinese');
  const themeLabel =
    mode === 'system' ? t('theme.system') :
    mode === 'light' ? t('theme.light') :
    t('theme.dark');

  return (
    <aside
      className={`flex h-screen flex-shrink-0 flex-col border-r border-ldvh-border bg-ldvh-panel transition-[width] duration-200 ease-in-out ${
        collapsed ? 'w-14' : 'w-56'
      }`}
    >
      <div className={`border-b border-ldvh-border ${collapsed ? 'px-2 py-3' : 'px-3 py-4'}`}>
        <div className={collapsed ? 'flex flex-col items-center gap-2' : 'flex items-center justify-between gap-2'}>
          <div className={`flex min-w-0 items-center ${collapsed ? 'justify-center' : 'gap-2'}`}>
            <div className="group relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-ldvh-accent/15" title={collapsed ? 'LDVH' : undefined}>
              <Shield size={18} className="text-ldvh-accent" />
              {collapsed && <IconTooltip label="LDVH" />}
            </div>
            {!collapsed && (
            <div className="min-w-0 flex-1">
              <div className="ldvh-card-title font-mono font-bold tracking-wide">LDVH</div>
                <div className="ldvh-caption whitespace-normal break-keep">
                  {t('logo.tagline')}
                </div>
              </div>
            )}
          </div>
          <button
            onClick={onToggle}
            title={collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')}
            aria-label={collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')}
            className="group relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
          >
            <PanelLeft size={16} className={collapsed ? 'rotate-180' : ''} />
            {collapsed && <IconTooltip label={t('nav.expandSidebar')} />}
          </button>
        </div>
      </div>
      <nav className={`flex-1 px-2 py-3 ${collapsed ? 'overflow-visible' : 'overflow-y-auto'}`}>
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                title={collapsed ? t(item.labelKey) : undefined}
                aria-label={collapsed ? t(item.labelKey) : undefined}
                className={({ isActive }) =>
                  `ldvh-card-title group relative flex items-center rounded-md transition-colors ${
                    collapsed ? 'h-10 justify-center px-0' : 'gap-2.5 px-3 py-2'
                  } ${
                    isActive
                      ? 'bg-ldvh-accent/10 text-ldvh-accent'
                      : 'text-ldvh-text-secondary hover:bg-ldvh-border/50 hover:text-ldvh-text-primary'
                  }`
                }
              >
                <item.icon size={16} className="flex-shrink-0" />
                {!collapsed && <span className="truncate">{t(item.labelKey)}</span>}
                {collapsed && <IconTooltip label={t(item.labelKey)} />}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className={`border-t border-ldvh-border ${collapsed ? 'px-2 py-3' : 'px-3 py-3'}`}>
        <div className={collapsed ? 'flex flex-col items-center gap-1' : 'flex items-center gap-1'}>
          <button
            onClick={() => setLocale(locale === 'zh' ? 'en' : 'zh')}
            title={languageLabel}
            aria-label={languageLabel}
            className={`ldvh-card-title group relative flex items-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary ${
              collapsed ? 'h-9 w-9 justify-center px-0' : 'flex-1 gap-2 px-3 py-1.5'
            }`}
          >
            <Globe size={16} />
            {!collapsed && (locale === 'zh' ? 'English' : '中文')}
            {collapsed && <IconTooltip label={languageLabel} />}
          </button>
          <button
            onClick={cycleTheme}
            title={themeLabel}
            aria-label={themeLabel}
            className="group relative flex h-9 w-9 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
          >
            <ThemeIcon mode={mode} />
            {collapsed && <IconTooltip label={themeLabel} />}
          </button>
        </div>
      </div>
    </aside>
  );
}
