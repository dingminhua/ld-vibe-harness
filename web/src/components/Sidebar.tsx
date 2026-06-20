import { NavLink } from 'react-router-dom';
import { useState } from 'react';
import type { ElementType } from 'react';
import {
  LayoutDashboard,
  Globe,
  FolderTree,
  Sun,
  Moon,
  Monitor,
  PanelLeft,
  type LucideProps,
} from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { useTheme } from '@/hooks/useTheme';
import type { LocaleKey } from '@/i18n/locales';
import { OBJECT_TYPE_ICONS } from '@/components/SemanticIcon';
import ldBrandMark from '@/assets/ld-brand-mark.svg';

type NavIcon = ElementType<LucideProps>;

const NAV_ITEMS: { to: string; labelKey?: LocaleKey; label?: { zh: string; en: string }; icon: NavIcon }[] = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/project-files', label: { zh: '文件', en: 'Files' }, icon: FolderTree },
  { to: '/objects/workarea', labelKey: 'nav.workareas', icon: OBJECT_TYPE_ICONS.workarea },
  { to: '/objects/workplan', labelKey: 'nav.workplans', icon: OBJECT_TYPE_ICONS.workplan },
  { to: '/objects/adr', labelKey: 'nav.adrs', icon: OBJECT_TYPE_ICONS.adr },
  { to: '/objects/pitfall', labelKey: 'nav.pitfalls', icon: OBJECT_TYPE_ICONS.pitfall },
  { to: '/objects/spark', labelKey: 'nav.sparks', icon: OBJECT_TYPE_ICONS.spark },
  { to: '/objects/study', labelKey: 'nav.studies', icon: OBJECT_TYPE_ICONS.study },
  { to: '/changelog', labelKey: 'nav.changelog', icon: OBJECT_TYPE_ICONS.changelog },
];

function getNavItemLabel(item: (typeof NAV_ITEMS)[number], locale: string, t: (key: LocaleKey) => string): string {
  if (item.labelKey) return t(item.labelKey);
  return locale === 'en' ? item.label?.en ?? '' : item.label?.zh ?? '';
}

function ThemeIcon({ mode }: { mode: 'system' | 'light' | 'dark' }) {
  if (mode === 'light') return <Sun size={16} />;
  if (mode === 'dark') return <Moon size={16} />;
  return <Monitor size={16} />;
}

function BrandMark() {
  return (
    <span
      className="flex h-7 w-7 items-center justify-center rounded-md bg-[#213330]"
      aria-hidden="true"
    >
      <img src={ldBrandMark} alt="" className="w-[17px]" />
    </span>
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
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { locale, setLocale, t } = useI18n();
  const { mode, cycleTheme } = useTheme();
  const [visibleTooltip, setVisibleTooltip] = useState<string | null>(null);
  const languageLabel = locale === 'zh' ? t('language.switchToEnglish') : t('language.switchToChinese');
  const sidebarToggleLabel = collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar');
  const themeLabel =
    mode === 'system' ? t('theme.system') :
    mode === 'light' ? t('theme.light') :
    t('theme.dark');

  return (
    <aside
      className={`flex h-screen flex-shrink-0 flex-col border-r border-ldvh-border bg-ldvh-panel transition-[width] duration-200 ease-in-out ${
        collapsed ? 'w-14' : 'w-[186px]'
      }`}
    >
      <div className={`border-b border-ldvh-border ${collapsed ? 'px-2 py-3' : 'px-3 py-4'}`}>
        <div className={collapsed ? 'flex flex-col items-center gap-2' : 'flex items-center gap-2'}>
          <div className={`flex min-w-0 items-center ${collapsed ? 'justify-center' : 'gap-2'}`}>
            <div
              onMouseEnter={() => setVisibleTooltip('brand')}
              onMouseLeave={() => setVisibleTooltip(null)}
              className="relative flex h-8 w-8 flex-shrink-0 items-center justify-center"
            >
              <BrandMark />
              {collapsed && <IconTooltip label="LDVH" visible={visibleTooltip === 'brand'} />}
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <div className="ldvh-caption whitespace-normal break-keep">
                  {t('logo.tagline')}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <nav className={`flex-1 px-2 py-3 ${collapsed ? 'overflow-visible' : 'overflow-y-auto'}`}>
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                aria-label={collapsed ? getNavItemLabel(item, locale, t) : undefined}
                onMouseEnter={() => setVisibleTooltip(`nav-${item.to}`)}
                onMouseLeave={() => setVisibleTooltip(null)}
                onFocus={() => setVisibleTooltip(`nav-${item.to}`)}
                onBlur={() => setVisibleTooltip(null)}
                onClick={() => setVisibleTooltip(null)}
                className={({ isActive }) =>
                  `ldvh-card-title relative flex items-center rounded-md transition-colors ${
                    collapsed ? 'h-10 justify-center px-0' : 'gap-2.5 px-3 py-2'
                  } ${
                    isActive
                      ? 'bg-ldvh-accent/10 text-ldvh-accent'
                      : 'text-ldvh-text-secondary hover:bg-ldvh-border/50 hover:text-ldvh-text-primary'
                  }`
                }
              >
                <item.icon size={16} className="flex-shrink-0" />
                {!collapsed && <span className="truncate">{getNavItemLabel(item, locale, t)}</span>}
                {collapsed && <IconTooltip label={getNavItemLabel(item, locale, t)} visible={visibleTooltip === `nav-${item.to}`} />}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className={`border-t border-ldvh-border ${collapsed ? 'px-2 py-3' : 'px-3 py-3'}`}>
        <div className={collapsed ? 'flex flex-col items-center gap-1' : 'flex items-center gap-1'}>
          <button
            onClick={() => {
              setVisibleTooltip(null);
              setLocale(locale === 'zh' ? 'en' : 'zh');
            }}
            onMouseEnter={() => setVisibleTooltip('language')}
            onMouseLeave={() => setVisibleTooltip(null)}
            onFocus={() => setVisibleTooltip('language')}
            onBlur={() => setVisibleTooltip(null)}
            aria-label={languageLabel}
            className={`ldvh-card-title relative flex items-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary ${
              collapsed ? 'h-9 w-9 justify-center px-0' : 'flex-1 gap-2 px-3 py-1.5'
            }`}
          >
            <Globe size={16} />
            {!collapsed && (locale === 'zh' ? t('language.english') : t('language.chinese'))}
            {collapsed && <IconTooltip label={languageLabel} visible={visibleTooltip === 'language'} />}
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
            <PanelLeft size={16} className={collapsed ? 'rotate-180' : ''} />
            <IconTooltip label={sidebarToggleLabel} visible={visibleTooltip === 'sidebar-toggle'} />
          </button>
        </div>
      </div>
    </aside>
  );
}
