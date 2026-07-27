import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('compact viewport keeps the primary navigation as an icon rail', () => {
  const layout = fs.readFileSync(path.resolve('src/components/Layout.tsx'), 'utf8');
  const sidebar = fs.readFileSync(path.resolve('src/components/Sidebar.tsx'), 'utf8');

  assert.match(layout, /className="flex flex-shrink-0 sm:hidden"\s*>\s*<Sidebar collapsed compact \/>/);
  assert.match(layout, /className="hidden flex-shrink-0 sm:block"\s*>\s*<Sidebar collapsed=\{sidebarCollapsed\}/);
  assert.match(sidebar, /const isCollapsed = compact \|\| collapsed;/);
  assert.match(sidebar, /isCollapsed \? 'w-14' : 'w-\[186px\]'/);
  assert.match(sidebar, /!compact && onToggle && \(/);
});

test('files, workspace changes, and commit records form one ordered navigation group', () => {
  const app = fs.readFileSync(path.resolve('src/App.tsx'), 'utf8');
  const sidebar = fs.readFileSync(path.resolve('src/components/Sidebar.tsx'), 'utf8');

  assert.match(app, /<Route path="\/changes" element=\{<Changes \/>\} \/>/);
  assert.match(
    sidebar,
    /\{ to: '\/project-files', labelKey: 'nav\.projectFiles'.*\},\s*\{ to: '\/changes', labelKey: 'nav\.changes'.*\},\s*\{ to: '\/changelog', labelKey: 'nav\.changelog'/s,
  );
});

test('settings is the final navigation entry and only exposes governed-project configuration', () => {
  const app = fs.readFileSync(path.resolve('src/App.tsx'), 'utf8');
  const sidebar = fs.readFileSync(path.resolve('src/components/Sidebar.tsx'), 'utf8');
  const settings = fs.readFileSync(path.resolve('src/pages/Settings.tsx'), 'utf8');

  assert.match(app, /<Route path="\/settings" element=\{<Settings \/>\} \/>/);
  assert.match(sidebar, /\{ to: '\/changelog'[\s\S]*\{ to: '\/settings', labelKey: 'nav\.settings'[\s\S]*\];/);
  assert.match(settings, /LDVH-GOVERNED-PROJECTS\.yaml/);
  assert.match(settings, /无需填写 Git 远程地址/);
  assert.match(settings, /验证为有效 Git 工作区/);
  assert.match(settings, /默认项目/);
  assert.match(settings, /保存默认项目/);
  assert.doesNotMatch(settings, /fetchProjectGit|fetchObject|saveObject/);
});

test('the governed project switcher lives beside the brand in global navigation', () => {
  const app = fs.readFileSync(path.resolve('src/App.tsx'), 'utf8');
  const sidebar = fs.readFileSync(path.resolve('src/components/Sidebar.tsx'), 'utf8');

  assert.match(app, /<ProjectScopeProvider>\s*<AppRoutes \/>\s*<\/ProjectScopeProvider>/);
  assert.match(sidebar, /<BrandMark \/>[\s\S]*<ProjectSwitcher collapsed=\{isCollapsed\} \/>/);
});

test('global project selection uses the configured default when no valid Human selection remains', () => {
  const context = fs.readFileSync(path.resolve('src/utils/projectContext.tsx'), 'utf8');

  assert.match(context, /result\.defaultProjectId/);
  assert.match(context, /nextProjects\.some\(\(project\) => project\.id === current\)/);
});

test('workspace changes reads status and diffs for the globally selected project', () => {
  const changes = fs.readFileSync(path.resolve('src/pages/Changes.tsx'), 'utf8');
  const controller = fs.readFileSync(path.resolve('src/pages/changes/useWorkspaceChanges.ts'), 'utf8');

  assert.match(changes, /const projectId = selectedProject\?\.id \?\? '';/);
  assert.match(changes, /useWorkspaceChanges\(projectId\)/);
  assert.match(controller, /fetchProjectGitStatus\(projectId\)/);
  assert.match(controller, /fetchProjectGitDiff\(entry\.projectId, entry\.path, entry\.status\)/);
});

test('workspace changes defaults to split on wide screens and unified below xl', () => {
  const changes = fs.readFileSync(path.resolve('src/pages/Changes.tsx'), 'utf8');

  assert.match(changes, /WIDE_DIFF_LAYOUT_QUERY = '\(min-width: 1280px\)'/);
  assert.match(changes, /mediaQuery\.matches \? 'split' : 'unified'/);
  assert.match(changes, /useState<DiffViewMode>\(getDefaultDiffViewMode\)/);
  assert.match(changes, /diffViewModeWasSelected\.current = true/);
});

test('project files is a focused browser without nested Git views or eager Git reads', () => {
  const filesPage = fs.readFileSync(path.resolve('src/pages/ProjectFiles.tsx'), 'utf8');
  const controller = fs.readFileSync(path.resolve('src/pages/project-files/useProjectFilesController.ts'), 'utf8');

  assert.doesNotMatch(filesPage, /role="tablist"|quickDirs|projectFiles\.(changesTab|historyTab|quickRoots)/);
  assert.match(controller, /fetchProjectFileEntries\(projectId, nextDir, nextShowHidden\)/);
  assert.doesNotMatch(controller, /fetchProjectGit(Status|Diff|Commits|CommitDetail|CommitFileDiff)/);
});

test('files and changes share a compact divided page toolbar', () => {
  const filesPage = fs.readFileSync(path.resolve('src/pages/ProjectFiles.tsx'), 'utf8');
  const changesPage = fs.readFileSync(path.resolve('src/pages/Changes.tsx'), 'utf8');
  const styles = fs.readFileSync(path.resolve('src/index.css'), 'utf8');

  for (const page of [filesPage, changesPage]) {
    assert.match(page, /ldvh-page-toolbar mb-4/);
    assert.match(page, /<PageHeader[^>]* compact \/>/);
    assert.match(page, /ldvh-page-toolbar-badge/);
    assert.match(page, /ldvh-page-toolbar-action/);
  }
  assert.match(styles, /\.ldvh-page-toolbar \{\s*@apply[^;]*border-b[^;]*pb-4;/s);
  assert.match(styles, /\.ldvh-page-toolbar-(?:badge|action) \{\s*@apply[^;]*h-8/s);
  assert.doesNotMatch(changesPage, /changes\.(activeProject|activeProjectHint|projectScopeHint)/);
});
