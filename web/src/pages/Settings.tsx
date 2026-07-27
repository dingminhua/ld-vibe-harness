import { FormEvent, useCallback, useEffect, useState } from 'react';
import { CheckCircle2, FolderPlus, Loader2, Save, ShieldCheck, Trash2 } from 'lucide-react';
import PageHeader from '@/components/PageHeader';
import { fetchGovernedProjectsSettings, saveGovernedProjectsSettings, verifyGovernedProjectsSettings, type GovernedProjectSetting, type GovernedProjectsSettingsData } from '@/utils/api';
import { useProjectScope } from '@/utils/projectContext';

const blankProject = (): GovernedProjectSetting => ({ id: '', path: '', name: '' });

export default function Settings() {
  const [settings, setSettings] = useState<GovernedProjectsSettingsData | null>(null);
  const [newProject, setNewProject] = useState<GovernedProjectSetting>(blankProject);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifiedMessage, setVerifiedMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { reloadProjects } = useProjectScope();

  const reload = useCallback(() => {
    setLoading(true); setError(null); setVerifiedMessage(null);
    fetchGovernedProjectsSettings().then(setSettings).catch((reason) => setError(reason.message)).finally(() => setLoading(false));
  }, []);
  useEffect(reload, [reload]);

  const save = async (projects: GovernedProjectSetting[], requestedDefaultProjectId = settings?.defaultProjectId ?? ''): Promise<boolean> => {
    if (!settings) return false;
    setSaving(true); setError(null);
    try {
      const next = await saveGovernedProjectsSettings(projects, settings.fingerprint, requestedDefaultProjectId);
      setSettings(next); reloadProjects(); setVerifiedMessage('保存成功，当前项目登记已通过 Git 工作区验证。');
      return true;
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setSaving(false); }
    return false;
  };

  const verify = async () => {
    setVerifying(true); setError(null); setVerifiedMessage(null);
    try {
      await verifyGovernedProjectsSettings();
      setVerifiedMessage('当前全部项目登记均已通过 Git 工作区验证。');
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setVerifying(false); }
  };

  const rename = (project: GovernedProjectSetting, name: string) => {
    const normalizedName = name.trim();
    if (!settings || normalizedName === (project.name ?? '')) return;
    void save(settings.projects.map((item) => item.id === project.id ? { ...item, ...(normalizedName ? { name: normalizedName } : { name: undefined }) } : item));
  };
  const remove = (project: GovernedProjectSetting) => {
    if (!settings || !window.confirm(`移除管辖项目“${project.name || project.id}”？这只会修改工作区配置。`)) return;
    const projects = settings.projects.filter((item) => item.id !== project.id);
    void save(projects, project.id === settings.defaultProjectId ? (projects[0]?.id ?? '') : settings.defaultProjectId);
  };
  const add = (event: FormEvent) => {
    event.preventDefault();
    if (!settings) return;
    void save([...settings.projects, newProject]).then((saved) => { if (saved) setNewProject(blankProject); });
  };

  return (
    <div className="mx-auto max-w-5xl px-5 py-7 sm:px-8">
      <PageHeader title="设置" subtitle="管理工作区的管辖项目配置" />
      <p className="ldvh-body-muted mt-2">这里只管理 LDVH-GOVERNED-PROJECTS.yaml 中的项目登记；不修改项目事实、Git 分支或执行状态。</p>
      <p className="ldvh-body-muted mt-1">无需填写 Git 远程地址。每个本地路径在保存时必须能现场验证为有效 Git 工作区；远程地址、分支和 HEAD 不参与管辖项目判定。</p>
      {loading ? <div className="flex justify-center py-16"><Loader2 className="animate-spin" /></div> : error ? (
        <div className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-300">{error}</div>
      ) : settings && <>
        <div className="mt-6 rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
          <div className="flex flex-wrap items-center justify-between gap-3"><p className="ldvh-caption-strong">管辖项目</p><button type="button" disabled={saving || verifying} onClick={() => void verify()} className="ldvh-card-title inline-flex items-center gap-2 rounded-md border border-ldvh-border px-3 py-2 text-ldvh-text-secondary hover:text-ldvh-text-primary disabled:opacity-50"><ShieldCheck size={15} />{verifying ? '正在验证…' : '验证当前配置'}</button></div>
          <p className="ldvh-meta mt-1 break-all">{settings.configPath}</p>
          {verifiedMessage && <p className="mt-3 flex items-center gap-2 text-sm text-emerald-500"><CheckCircle2 size={16} />{verifiedMessage}</p>}
          <div className="mt-4 grid max-w-sm gap-2"><label className="grid gap-1"><span className="ldvh-meta">默认项目</span><select value={settings.defaultProjectId} disabled={saving || !settings.projects.length} onChange={(event) => void save(settings.projects, event.target.value)} className="rounded-md border border-ldvh-border bg-ldvh-bg px-2.5 py-2 text-sm outline-none focus:border-ldvh-accent">{settings.projects.map((project) => <option key={project.id} value={project.id}>{project.name || project.id}</option>)}</select></label><div className="flex items-center gap-2"><button type="button" disabled={saving || !settings.projects.length} onClick={() => void save(settings.projects, settings.defaultProjectId)} className="ldvh-card-title inline-flex w-fit items-center gap-2 rounded-md border border-ldvh-border px-3 py-2 text-ldvh-text-secondary hover:text-ldvh-text-primary disabled:opacity-50"><Save size={15} />保存默认项目</button><span className="ldvh-meta">{settings.hasExplicitDefault ? '启动时默认选中此项目。' : '当前按配置列表首项临时选中。'}</span></div></div>
          <div className="mt-4 grid gap-3">
            {settings.projects.map((project) => <ProjectRow key={project.id} project={project} saving={saving} onRename={rename} onRemove={remove} />)}
          </div>
        </div>
        <form onSubmit={add} className="mt-5 rounded-xl border border-ldvh-border bg-ldvh-panel p-4">
          <div className="flex items-center gap-2"><FolderPlus size={16} /><p className="ldvh-caption-strong">添加项目</p></div>
          <div className="mt-4 grid gap-3 lg:grid-cols-3">
            <Field label="稳定 ID" value={newProject.id} onChange={(id) => setNewProject((value) => ({ ...value, id }))} required />
            <Field label="本地 Git 工作区路径" value={newProject.path} onChange={(path) => setNewProject((value) => ({ ...value, path }))} required />
            <Field label="简称" value={newProject.name ?? ''} onChange={(name) => setNewProject((value) => ({ ...value, name }))} />
          </div>
          <button disabled={saving} className="ldvh-card-title mt-4 inline-flex items-center gap-2 rounded-md bg-ldvh-accent px-3 py-2 text-white disabled:opacity-50"><Save size={15} />添加并验证 Git 项目</button>
        </form>
      </>}
    </div>
  );
}

function ProjectRow({ project, saving, onRename, onRemove }: { project: GovernedProjectSetting; saving: boolean; onRename: (project: GovernedProjectSetting, name: string) => void; onRemove: (project: GovernedProjectSetting) => void }) {
  const [name, setName] = useState(project.name ?? '');
  return <div className="rounded-lg border border-ldvh-border p-3"><div className="grid gap-3 lg:grid-cols-[1fr_1.5fr_1fr_auto] lg:items-end"><Field label="ID" value={project.id} readOnly /><Field label="路径" value={project.path} readOnly /><Field label="简称" value={name} onChange={setName} /><div className="flex gap-2"><button type="button" disabled={saving} onClick={() => onRename(project, name)} className="rounded-md border border-ldvh-border p-2 text-ldvh-text-secondary hover:text-ldvh-text-primary"><Save size={15} /></button><button type="button" disabled={saving} onClick={() => onRemove(project)} className="rounded-md border border-red-500/30 p-2 text-red-400"><Trash2 size={15} /></button></div></div></div>;
}

function Field({ label, value, onChange, required, readOnly }: { label: string; value: string; onChange?: (value: string) => void; required?: boolean; readOnly?: boolean }) {
  return <label className="grid gap-1"><span className="ldvh-meta">{label}</span><input value={value} required={required} readOnly={readOnly} onChange={(event) => onChange?.(event.target.value)} className="rounded-md border border-ldvh-border bg-ldvh-bg px-2.5 py-2 text-sm outline-none focus:border-ldvh-accent" /></label>;
}
