import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import type { ElementType } from 'react';
import {
  LayoutDashboard,
  Globe,
  FolderTree,
  GitPullRequestArrow,
  Sun,
  Moon,
  Monitor,
  PanelLeft,
  type LucideProps,
} from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { useTheme } from '@/hooks/useTheme';
import { getLanguageSwitchKey, getOppositeLanguageNameKey, getOppositeLocale, type LocaleKey } from '@/i18n/locales';
import { OBJECT_TYPE_ICONS } from '@/components/SemanticIcon';
import ProjectSwitcher from '@/components/ProjectSwitcher';
import ldvhPluginIcon from '@/assets/ldvh-plugin-icon.png';

type NavIcon = ElementType<LucideProps>;

const NAV_ITEMS: { to: string; labelKey: LocaleKey; icon: NavIcon }[] = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/objects/spark', labelKey: 'nav.sparks', icon: OBJECT_TYPE_ICONS.spark },
  { to: '/objects/workcase', labelKey: 'nav.workcases', icon: OBJECT_TYPE_ICONS.workcase },
  { to: '/objects/adr', labelKey: 'nav.adrs', icon: OBJECT_TYPE_ICONS.adr },
  { to: '/objects/pitfall', labelKey: 'nav.pitfalls', icon: OBJECT_TYPE_ICONS.pitfall },
  { to: '/objects/study', labelKey: 'nav.studies', icon: OBJECT_TYPE_ICONS.study },
  { to: '/project-files', labelKey: 'nav.projectFiles', icon: FolderTree },
  { to: '/changes', labelKey: 'nav.changes', icon: GitPullRequestArrow },
  { to: '/changelog', labelKey: 'nav.changelog', icon: OBJECT_TYPE_ICONS.changelog },
];

function getNavItemLabel(item: (typeof NAV_ITEMS)[number], t: (key: LocaleKey) => string): string {
  return t(item.labelKey);
}

function ThemeIcon({ mode }: { mode: 'system' | 'light' | 'dark' }) {
  if (mode === 'light') return <Sun size={16} />;
  if (mode === 'dark') return <Moon size={16} />;
  return <Monitor size={16} />;
}

function BrandMark() {
  return (
    <img src={ldvhPluginIcon} alt="" className="h-9 w-9 rounded-md" aria-hidden="true" />
  );
}

function IconTooltip({ label, visible }: { label: string; visible: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={`ldvh-chip pointer-events-none absolute left-full top-1/2 z-50 ml-2 -translate-y-1/2 whitespace-nowrap rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1 text-ldvh-text-primary shadow-lg shadow-black/10 transition-opacity ${
        visible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {label}
    </span>
  );
}

interface SidebarProps {
  collapsed: boolean;
  compact?: boolean;
  onToggle?: () => void;
}

export default function Sidebar({ collapsed, compact = false, onToggle }: SidebarProps) {
  const { locale, setLocale, t } = useI18n();
  const { mode, cycleTheme } = useTheme();
  const [visibleTooltip, setVisibleTooltip] = useState<string | null>(null);
  const isCollapsed = compact || collapsed;
  const languageLabel = t(getLanguageSwitchKey(locale));
  const sidebarToggleLabel = isCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar');
  const themeLabel =
    mode === 'system' ? t('theme.system') :
    mode === 'light' ? t('theme.light') :
    t('theme.dark');

  return (
    <aside
      className={`flex h-screen flex-shrink-0 flex-col border-r border-ldvh-border bg-ldvh-panel transition-[width] duration-200 ease-in-out ${
        isCollapsed ? 'w-14' : 'w-[186px]'
      }`}
    >
      <div className={`border-b border-ldvh-border ${isCollapsed ? 'px-2 py-3' : 'px-3 py-4'}`}>
        <div className={isCollapsed ? 'flex flex-col items-center gap-2' : 'flex min-w-0 items-center gap-2'}>
          <div className={`flex min-w-0 items-center ${isCollapsed ? 'justify-center' : ''}`}>
            <div
              onMouseEnter={() => setVisibleTooltip('brand')}
              onMouseLeave={() => setVisibleTooltip(null)}
              className="relative flex h-10 w-10 flex-shrink-0 items-center justify-center"
            >
              <BrandMark />
              {isCollapsed && <IconTooltip label="LDVH" visible={visibleTooltip === 'brand'} />}
            </div>
          </div>
          <ProjectSwitcher collapsed={isCollapsed} />
        </div>
      </div>
      <nav className={`flex-1 px-2 py-3 ${isCollapsed && !compact ? 'overflow-visible' : 'overflow-y-auto'}`}>
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                aria-label={isCollapsed ? getNavItemLabel(item, t) : undefined}
                onMouseEnter={() => setVisibleTooltip(`nav-${item.to}`)}
                onMouseLeave={() => setVisibleTooltip(null)}
                onFocus={() => setVisibleTooltip(`nav-${item.to}`)}
                onBlur={() => setVisibleTooltip(null)}
                onClick={() => setVisibleTooltip(null)}
                className={({ isActive }) =>
                  `ldvh-card-title relative flex items-center rounded-md transition-colors ${
                    isCollapsed ? 'h-10 justify-center px-0' : 'gap-2.5 px-3 py-2'
                  } ${
                    isActive
                      ? 'bg-ldvh-accent/10 text-ldvh-accent'
                      : 'text-ldvh-text-secondary hover:bg-ldvh-border/50 hover:text-ldvh-text-primary'
                  }`
                }
              >
                <item.icon size={16} className="flex-shrink-0" />
                {!isCollapsed && <span className="truncate">{getNavItemLabel(item, t)}</span>}
                {isCollapsed && <IconTooltip label={getNavItemLabel(item, t)} visible={visibleTooltip === `nav-${item.to}`} />}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className={`border-t border-ldvh-border ${isCollapsed ? 'px-2 py-3' : 'px-3 py-3'}`}>
        <div className={isCollapsed ? 'flex flex-col items-center gap-1' : 'flex items-center gap-1'}>
          <button
            onClick={() => {
              setVisibleTooltip(null);
              setLocale(getOppositeLocale(locale));
            }}
            onMouseEnter={() => setVisibleTooltip('language')}
            onMouseLeave={() => setVisibleTooltip(null)}
            onFocus={() => setVisibleTooltip('language')}
            onBlur={() => setVisibleTooltip(null)}
            aria-label={languageLabel}
            className={`ldvh-card-title relative flex items-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary ${
              isCollapsed ? 'h-9 w-9 justify-center px-0' : 'flex-1 gap-2 px-3 py-1.5'
            }`}
          >
            <Globe size={16} />
            {!isCollapsed && t(getOppositeLanguageNameKey(locale))}
            {isCollapsed && <IconTooltip label={languageLabel} visible={visibleTooltip === 'language'} />}
          </button>
          <button
            onClick={() => {
              setVisibleTooltip(null);
              cycleTheme();
            }}
            onMouseEnter={() => setVisibleTooltip('theme')}
            onMouseLeave={() => setVisibleTooltip(null)}
            onFocus={() => setVisibleTooltip('theme')}
            onBlur={() => setVisibleTooltip(null)}
            aria-label={themeLabel}
            className="relative flex h-9 w-9 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
          >
            <ThemeIcon mode={mode} />
            <IconTooltip label={themeLabel} visible={visibleTooltip === 'theme'} />
          </button>
          {!compact && onToggle && (
            <button
              onClick={() => {
                setVisibleTooltip(null);
                onToggle();
              }}
              onMouseEnter={() => setVisibleTooltip('sidebar-toggle')}
              onMouseLeave={() => setVisibleTooltip(null)}
              onFocus={() => setVisibleTooltip('sidebar-toggle')}
              onBlur={() => setVisibleTooltip(null)}
              aria-label={sidebarToggleLabel}
              className="relative flex h-9 w-9 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
            >
              <PanelLeft size={16} className={isCollapsed ? 'rotate-180' : ''} />
              <IconTooltip label={sidebarToggleLabel} visible={visibleTooltip === 'sidebar-toggle'} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
