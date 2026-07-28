import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, FolderGit2, Loader2, RefreshCcw } from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { useProjectScope } from '@/utils/projectContext';

export default function ProjectSwitcher({ collapsed }: { collapsed: boolean }) {
  const { t } = useI18n();
  const { projects, selectedProject, selectedProjectId, loading, error, selectProject, reloadProjects, refreshData } = useProjectScope();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerLabel = selectedProject?.name || t('projectSwitcher.choose');

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className={`relative min-w-0 ${collapsed ? '' : 'flex-1'}`}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('projectSwitcher.label')}
        title={collapsed ? triggerLabel : undefined}
        onClick={() => setOpen((current) => !current)}
        className={`flex min-w-0 items-center rounded-md border transition-colors ${
          open
            ? 'border-ldvh-accent/40 bg-ldvh-accent/10 text-ldvh-accent'
            : 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary hover:border-ldvh-accent/35 hover:text-ldvh-text-primary'
        } ${collapsed ? 'h-9 w-9 justify-center' : 'h-10 w-full gap-2 px-2.5 text-left'}`}
      >
        {collapsed ? (
          <FolderGit2 size={15} className="shrink-0" />
        ) : (
          <>
            <span className="ldvh-caption-strong min-w-0 flex-1 truncate">{triggerLabel}</span>
            <ChevronDown size={13} className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
          </>
        )}
      </button>

      {open && (
        <div
          role="listbox"
          aria-label={t('projectSwitcher.label')}
          className={`absolute z-[70] w-72 overflow-hidden rounded-lg border border-ldvh-border bg-ldvh-panel shadow-xl shadow-black/20 ${
            collapsed ? 'left-full top-0 ml-2' : 'left-0 top-full mt-2'
          }`}
        >
          <div className="flex items-center justify-between gap-2 border-b border-ldvh-border px-3 py-2.5">
            <div className="min-w-0">
              <p className="ldvh-caption-strong">{t('projectSwitcher.label')}</p>
              <p className="ldvh-meta mt-0.5">{t('projectSwitcher.scopeHint')}</p>
            </div>
            <button
              type="button"
              onClick={() => { reloadProjects(); refreshData(); }}
              disabled={loading}
              aria-label={t('projectSwitcher.reload')}
              title={t('projectSwitcher.reload')}
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/40 hover:text-ldvh-text-primary disabled:opacity-50"
            >
              <RefreshCcw size={13} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>

          <div className="max-h-80 overflow-y-auto p-2">
            {loading ? (
              <div className="ldvh-body-muted flex items-center justify-center gap-2 px-3 py-6">
                <Loader2 size={14} className="animate-spin" />
                {t('projectSwitcher.loading')}
              </div>
            ) : error ? (
              <div className="px-3 py-4">
                <p className="ldvh-body-muted text-red-400">{t('projectSwitcher.loadFailed')}</p>
                <p className="ldvh-meta mt-1 break-words">{error}</p>
              </div>
            ) : projects.length === 0 ? (
              <p className="ldvh-body-muted px-3 py-6 text-center">{t('projectSwitcher.noProjects')}</p>
            ) : (
              projects.map((project) => {
                const selected = project.id === selectedProjectId;
                return (
                  <button
                    key={project.id}
                    type="button"
                    role="option"
                    aria-selected={selected}
                    onClick={() => {
                      selectProject(project.id);
                      setOpen(false);
                    }}
                    className={`flex w-full min-w-0 items-start gap-2 rounded-md px-2.5 py-2 text-left transition-colors ${
                      selected
                        ? 'bg-ldvh-accent/10 text-ldvh-accent'
                        : 'text-ldvh-text-primary hover:bg-ldvh-border/35'
                    }`}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="ldvh-card-title block truncate">{project.name || project.id}</span>
                      <span className="ldvh-meta mt-0.5 block truncate">{project.path}</span>
                    </span>
                    {selected && <Check size={14} className="mt-0.5 shrink-0" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
