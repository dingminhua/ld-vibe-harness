import { execFile } from 'child_process'
import path from 'path'
import { LDVH_ROOT, LDVH_WORKSPACE_ROOT } from './pytools.js'

export const MAX_FILE_BYTES = 300 * 1024
export const MAX_DIRECTORY_ENTRIES = 500
export const TEXT_SAMPLE_BYTES = 8192

export const EXCLUDED_DIRS = new Set([
  '.git',
  'node_modules',
  'dist',
  'build',
  '.next',
  '.turbo',
  '.cache',
  '__pycache__',
  '.pytest_cache',
  '.venv',
  'venv',
])

type GovernanceProjectIdentity = {
  project_id: string
  git_worktree_root: string
  git_common_dir: string
}

export type GovernedProject = {
  id: string
  name: string
  description: string
  path: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function helperExecutable(): string {
  if (process.env.LDVH_HELPER_EXECUTABLE) return path.resolve(process.env.LDVH_HELPER_EXECUTABLE)
  return process.platform === 'win32'
    ? path.join(LDVH_ROOT, '.venv', 'Scripts', 'ldvh.exe')
    : path.join(LDVH_ROOT, '.venv', 'bin', 'ldvh')
}

function invokeGovernanceScope(): Promise<Record<string, unknown>> {
  const locator = path.resolve(process.env.LDVH_WEB_WORKTREE_LOCATOR || LDVH_ROOT)
  const workspaceRoot = path.resolve(process.env.LDVH_WORKSPACE_ROOT || LDVH_WORKSPACE_ROOT)
  const request = JSON.stringify({
    work_object_locators: [locator],
    arguments: { workspace_root: workspaceRoot },
    response_profile: 'compact',
  })
  return new Promise((resolve, reject) => {
    const child = execFile(
      helperExecutable(),
      ['call', 'resolve-governance-scope'],
      { cwd: locator, maxBuffer: 10 * 1024 * 1024 },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`Governance resolver unavailable: ${stderr.trim() || error.message}`))
          return
        }
        try {
          const parsed: unknown = JSON.parse(stdout)
          if (!isRecord(parsed)) throw new Error('response is not an object')
          resolve(parsed)
        } catch (parseError) {
          reject(new Error(`Governance resolver returned invalid JSON: ${parseError instanceof Error ? parseError.message : String(parseError)}`))
        }
      },
    )
    child.stdin?.end(request)
  })
}

function verifiedGovernanceProjects(response: Record<string, unknown>): GovernedProject[] {
  if (response.outcome !== 'ok' || !isRecord(response.result)) {
    throw new Error(`Governance resolution did not complete: ${String(response.outcome || 'unknown')}`)
  }
  const result = response.result
  if (result.config_status !== 'valid' || result.scope_status !== 'governed_single') {
    throw new Error(`Governance resolution is not verified: config=${String(result.config_status)} scope=${String(result.scope_status)}`)
  }
  if (!Array.isArray(result.object_resolutions) || result.object_resolutions.length !== 1) {
    throw new Error('Governance resolution must contain exactly one requested worktree')
  }
  const current = result.object_resolutions[0]
  if (!isRecord(current)
    || current.status !== 'governed'
    || typeof current.governed_project_id !== 'string'
    || typeof current.git_worktree_root !== 'string'
    || typeof current.git_common_dir !== 'string'
    || !path.isAbsolute(current.git_worktree_root)
    || !path.isAbsolute(current.git_common_dir)) {
    throw new Error('Governance resolution did not verify the governed project, worktree, and common-dir')
  }

  const identities = new Map<string, GovernanceProjectIdentity>()
  if (Array.isArray(current.identity_evidence)) {
    for (const evidence of current.identity_evidence) {
      if (!isRecord(evidence) || evidence.kind !== 'registered_project_git_identity' || !isRecord(evidence.details)) continue
      const details = evidence.details
      if (details.status !== 'git_worktree'
        || typeof details.project_id !== 'string'
        || typeof details.git_worktree_root !== 'string'
        || typeof details.git_common_dir !== 'string'
        || !path.isAbsolute(details.git_worktree_root)
        || !path.isAbsolute(details.git_common_dir)) continue
      identities.set(details.project_id, {
        project_id: details.project_id,
        git_worktree_root: details.git_worktree_root,
        git_common_dir: details.git_common_dir,
      })
    }
  }
  identities.set(current.governed_project_id, {
    project_id: current.governed_project_id,
    git_worktree_root: current.git_worktree_root,
    git_common_dir: current.git_common_dir,
  })
  if (identities.size === 0) throw new Error('Governance resolution contained no verified projects')

  return [...identities.values()]
    .sort((left, right) => left.project_id.localeCompare(right.project_id))
    .map((identity) => ({
      id: identity.project_id,
      name: identity.project_id,
      description: '由 Code 管辖解析确认的 Git worktree',
      path: path.resolve(identity.git_worktree_root),
    }))
}

export type FileKind = 'directory' | 'markdown' | 'yaml' | 'svg' | 'text' | 'binary'

export function runCommand(command: string, args: string[], cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(command, args, { cwd, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(stderr?.trim() || error.message))
        return
      }
      resolve(stdout)
    })
  })
}

export function isInside(basePath: string, targetPath: string): boolean {
  const relative = path.relative(basePath, targetPath)
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))
}

export function normalizeProjectPath(rawPath: unknown, baseDir = LDVH_ROOT): string {
  const value = String(rawPath || '').trim()
  if (!value) return baseDir
  return path.resolve(path.isAbsolute(value) ? value : path.join(baseDir, value))
}

export async function loadProjects(): Promise<GovernedProject[]> {
  return verifiedGovernanceProjects(await invokeGovernanceScope())
}

export async function getProject(projectId: string): Promise<GovernedProject | null> {
  const projects = await loadProjects()
  return projects.find((project) => project.id === projectId) ?? null
}

export function resolveProjectTarget(project: GovernedProject, relativePath: string): string | null {
  if (relativePath.includes('\0')) return null
  const projectRoot = path.resolve(project.path)
  const target = path.resolve(projectRoot, relativePath || '.')
  return isInside(projectRoot, target) ? target : null
}

export function toProjectRelative(project: GovernedProject, absolutePath: string): string {
  const relative = path.relative(path.resolve(project.path), absolutePath)
  return relative === '' ? '' : relative.split(path.sep).join('/')
}

export function detectKind(name: string, isDirectory: boolean, sample?: Buffer): FileKind {
  if (isDirectory) return 'directory'
  if (/\.(md|markdown)$/i.test(name)) return 'markdown'
  if (/\.(ya?ml)$/i.test(name)) return 'yaml'
  if (/\.svg$/i.test(name)) return 'svg'
  if (sample?.includes(0)) return 'binary'
  if (/\.(txt|json|ts|tsx|js|jsx|css|html|py|sh|toml|lock|gitignore|env|csv|xml)$/i.test(name)) return 'text'
  return sample?.includes(0) ? 'binary' : 'text'
}

export function isHiddenPath(relativePath: string): boolean {
  return relativePath.split('/').some((part) => part.startsWith('.') && part.length > 1)
}

export function parseGitStatusLine(project: GovernedProject, line: string) {
  const status = line.slice(0, 2)
  const rawPath = line.slice(3).trim()
  const pathParts = rawPath.includes(' -> ') ? rawPath.split(' -> ') : [rawPath]
  const filePath = pathParts[pathParts.length - 1]
  return {
    projectId: project.id,
    status,
    path: filePath,
    absolutePath: path.join(project.path, filePath),
    staged: status[0] !== ' ' && status[0] !== '?',
    unstaged: status[1] !== ' ' || status === '??',
  }
}

export function parseCommitFileLine(project: GovernedProject, line: string) {
  const [status = '', ...pathParts] = line.split('\t')
  const filePath = pathParts[pathParts.length - 1] || ''
  return {
    status,
    path: filePath,
    absolutePath: path.join(project.path, filePath),
  }
}
