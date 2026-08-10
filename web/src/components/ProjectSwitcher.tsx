import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, FolderGit2, GitBranch, Loader2 } from 'lucide-react';
import { useI18n } from '@/i18n/context';
import { useProjectScope } from '@/utils/projectContext';

export default function ProjectSwitcher({ collapsed }: { collapsed: boolean }) {
  const { t } = useI18n();
  const { projects, selectedProject, selectedProjectId, selectedWorktree, selectedWorktreePath, loading, error, selectProject, reloadProjects } = useProjectScope();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerLabel = selectedProject?.name || t('projectSwitcher.choose');
  const triggerBranch = selectedWorktree?.branch || (selectedProject ? t('projectSwitcher.detached') : '');

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
        title={collapsed ? `${triggerLabel}${triggerBranch ? ` · ${triggerBranch}` : ''}` : undefined}
        onClick={() => setOpen((current) => {
          const next = !current;
          if (next) reloadProjects();
          return next;
        })}
        className={`flex min-w-0 items-center rounded-md border transition-colors ${
          open
            ? 'border-ldvh-accent/40 bg-ldvh-accent/10 text-ldvh-accent'
            : 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary hover:border-ldvh-accent/35 hover:text-ldvh-text-primary'
        } ${collapsed ? 'h-9 w-9 justify-center' : 'h-12 w-full gap-2 px-2.5 text-left'}`}
      >
        {collapsed ? (
          <FolderGit2 size={15} className="shrink-0" />
        ) : (
          <>
            <span className="min-w-0 flex-1">
              <span className="ldvh-caption-strong block truncate">{triggerLabel}</span>
              {triggerBranch && <span className="ldvh-meta mt-0.5 flex items-center gap-1 truncate"><GitBranch size={11} className="shrink-0" />{triggerBranch}</span>}
            </span>
            <ChevronDown size={13} className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
          </>
        )}
      </button>

      {open && (
        <div
          role="listbox"
          aria-label={t('projectSwitcher.label')}
          className={`absolute z-[70] w-[22rem] overflow-hidden rounded-xl border border-ldvh-border bg-ldvh-panel shadow-xl shadow-black/20 ${
            collapsed ? 'left-full top-0 ml-2' : 'left-0 top-full mt-2'
          }`}
        >
          <div className="border-b border-ldvh-border px-3 py-2.5">
            <div className="min-w-0">
              <p className="ldvh-caption-strong">{t('projectSwitcher.label')}</p>
              <p className="ldvh-meta mt-0.5">{t('projectSwitcher.worktreeScopeHint')}</p>
            </div>
          </div>

          <div className="max-h-[min(70vh,34rem)] overflow-y-auto p-2.5">
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
              <div className="grid gap-2.5">
              {projects.map((project) => {
                const worktrees = project.worktrees.length > 0
                  ? project.worktrees
                  : [{ path: project.path, isMain: true }];
                return (
                  <section key={project.id} className="overflow-hidden rounded-lg border border-ldvh-border bg-ldvh-bg/35">
                    <div className="flex min-w-0 items-center gap-2 border-b border-ldvh-accent/35 bg-ldvh-accent/20 px-3 py-2.5">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-ldvh-accent/35 bg-ldvh-accent/25 text-ldvh-accent">
                        <FolderGit2 size={15} />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="ldvh-caption-strong block truncate text-ldvh-text-primary">{project.name || project.id}</span>
                        <span className="ldvh-meta mt-0.5 block truncate">{project.id}</span>
                      </span>
                    </div>
                    <div className="grid gap-1 p-1.5">
                    {worktrees.map((worktree) => {
                      const selected = project.id === selectedProjectId && worktree.path === selectedWorktreePath;
                      const branch = worktree.branch || t('projectSwitcher.detached');
                      return (
                        <button
                          key={worktree.path}
                          type="button"
                          role="option"
                          aria-selected={selected}
                          title={worktree.path}
                          onClick={() => {
                            selectProject(project.id, worktree.path);
                            setOpen(false);
                          }}
                          className={`group flex w-full min-w-0 items-center gap-2.5 rounded-md border px-2.5 py-2 text-left transition-colors ${
                            selected
                              ? 'border-ldvh-accent/20 bg-ldvh-accent/5 text-ldvh-text-primary'
                              : 'border-transparent text-ldvh-text-primary hover:border-ldvh-border hover:bg-ldvh-panel'
                          }`}
                        >
                          <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${selected ? 'bg-ldvh-accent/10 text-ldvh-accent' : 'bg-ldvh-border/25 text-ldvh-text-secondary group-hover:text-ldvh-text-primary'}`}>
                            <GitBranch size={13} />
                          </span>
                          <span className="ldvh-card-title flex min-w-0 flex-1 items-center gap-2">
                            <span className="truncate">{branch}</span>
                            {worktree.isMain && <span className="shrink-0 rounded-full border border-ldvh-accent/25 bg-ldvh-panel px-1.5 py-0.5 text-[10px] font-medium leading-none text-ldvh-accent">{t('projectSwitcher.mainWorktree')}</span>}
                          </span>
                          {selected && <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-ldvh-accent/30 text-ldvh-accent"><Check size={12} strokeWidth={3} /></span>}
                        </button>
                      );
                    })}
                    </div>
                  </section>
                );
              })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
