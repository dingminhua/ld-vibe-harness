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
} from 'lucide-react';
import { useI18n } from '@/i18n/context';
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

export default function Sidebar() {
  const { locale, setLocale, t } = useI18n();

  return (
    <aside className="flex h-screen w-56 flex-shrink-0 flex-col border-r border-ldvh-border bg-ldvh-panel">
      <div className="border-b border-ldvh-border px-4 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-ldvh-accent/15">
            <Shield size={18} className="text-ldvh-accent" />
          </div>
          <div>
            <div className="font-mono text-sm font-bold text-ldvh-text-primary tracking-wide">LDVH</div>
            <div className="text-[10px] leading-tight text-ldvh-text-secondary">
              {t('logo.tagline')}
            </div>
          </div>
        </div>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-ldvh-accent/10 text-ldvh-accent'
                      : 'text-ldvh-text-secondary hover:bg-ldvh-border/50 hover:text-ldvh-text-primary'
                  }`
                }
              >
                <item.icon size={16} />
                {t(item.labelKey)}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="border-t border-ldvh-border px-3 py-3">
        <button
          onClick={() => setLocale(locale === 'zh' ? 'en' : 'zh')}
          className="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-sm text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/50 hover:text-ldvh-text-primary"
        >
          <Globe size={16} />
          {locale === 'zh' ? 'English' : '中文'}
        </button>
      </div>
    </aside>
  );
}
