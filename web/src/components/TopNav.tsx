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
  Sun,
  Moon,
  Monitor,
} from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { useTheme } from '@/hooks/useTheme';
import type { LocaleKey } from '@/i18n/locales';

const NAV_ITEMS: { to: string; labelKey: LocaleKey; icon: typeof LayoutDashboard }[] = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/objects/intent', labelKey: 'nav.intents', icon: Lightbulb },
  { to: '/objects/task', labelKey: 'nav.tasks', icon: Target },
  { to: '/objects/adr', labelKey: 'nav.adrs', icon: GitBranch },
  { to: '/objects/pitfall', labelKey: 'nav.pitfalls', icon: Bug },
  { to: '/objects/memo', labelKey: 'nav.memos', icon: StickyNote },
  { to: '/objects/profile', labelKey: 'nav.profiles', icon: BookOpen },
  { to: '/validate', labelKey: 'nav.validate', icon: Shield },
  { to: '/changelog', labelKey: 'nav.changelog', icon: ClipboardCheck },
];

function ThemeIcon({ mode }: { mode: 'system' | 'light' | 'dark' }) {
  if (mode === 'light') return <Sun size={14} />;
  if (mode === 'dark') return <Moon size={14} />;
  return <Monitor size={14} />;
}

export default function TopNav() {
  const { locale, setLocale, t } = useI18n();
  const { mode, cycleTheme } = useTheme();

  return (
    <header className="flex h-12 items-center justify-between border-b border-ldvh-border bg-ldvh-panel px-4">
      {/* Logo */}
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-ldvh-accent/15">
          <Shield size={14} className="text-ldvh-accent" />
        </div>
        <span className="font-mono text-sm font-bold text-ldvh-text-primary tracking-wide">LDVH</span>
        <span className="hidden text-[10px] text-ldvh-text-secondary lg:inline">{t('logo.tagline')}</span>
      </div>

      {/* Nav links */}
      <nav className="flex items-center gap-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition-colors ${
                isActive
                  ? 'bg-ldvh-accent/10 text-ldvh-accent'
                  : 'text-ldvh-text-secondary hover:bg-ldvh-border/50 hover:text-ldvh-text-primary'
              }`
            }
          >
            <item.icon size={14} />
            {t(item.labelKey)}
          </NavLink>
        ))}
      </nav>

      {/* Controls */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => setLocale(locale === 'zh' ? 'en' : 'zh')}
          title={locale === 'zh' ? 'Switch to English' : '切换到中文'}
          className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
        >
          <Globe size={14} />
          {locale === 'zh' ? 'EN' : '中'}
        </button>
        <button
          onClick={cycleTheme}
          title={mode === 'system' ? '跟随系统' : mode === 'light' ? '浅色模式' : '深色模式'}
          className="flex items-center justify-center rounded-md p-1.5 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
        >
          <ThemeIcon mode={mode} />
        </button>
      </div>
    </header>
  );
}
