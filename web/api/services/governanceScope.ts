import { execFile } from 'node:child_process'
import { realpathSync } from 'node:fs'
import path from 'node:path'
import { LDVH_ROOT, LDVH_WORKSPACE_ROOT } from './pytools.js'

export type WebGovernedProject = {
  id: string
  path: string
  gitCommonDir: string
}

type GovernanceProjectIdentity = {
  project_id: string
  git_worktree_root: string
  git_common_dir: string
}

export class WebGovernanceError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'WebGovernanceError'
  }
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

function configuredLocator(): string {
  const raw = process.env.LDVH_WEB_WORKTREE_LOCATOR || LDVH_ROOT
  return path.resolve(raw)
}

function configuredWorkspaceRoot(): string {
  // Use the shared workspace setting first, matching the Project Files and
  // Helper contract. The older Web-specific name remains only as fallback.
  const raw = process.env.LDVH_WORKSPACE_ROOT || process.env.LDVH_WEB_WORKSPACE_ROOT || LDVH_WORKSPACE_ROOT
  return path.resolve(raw)
}

function normalizedExistingPath(value: string): string {
  const resolved = path.resolve(value)
  try { return realpathSync.native(resolved) } catch { return resolved }
}

function invokeGovernanceScope(locator: string, workspaceRoot: string): Promise<Record<string, unknown>> {
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
          reject(new WebGovernanceError(`Governance resolver unavailable: ${stderr.trim() || error.message}`))
          return
        }
        try {
          const parsed: unknown = JSON.parse(stdout)
          if (!isRecord(parsed)) throw new Error('response is not an object')
          resolve(parsed)
        } catch (parseError) {
          reject(new WebGovernanceError(`Governance resolver returned invalid JSON: ${parseError instanceof Error ? parseError.message : String(parseError)}`))
        }
      },
    )
    child.stdin?.end(request)
  })
}

/** Verify a candidate configuration without interpreting it as a current fact read. */
export async function verifyWebGovernanceConfiguration(): Promise<void> {
  const response = await invokeGovernanceScope(configuredWorkspaceRoot(), configuredWorkspaceRoot())
  if (response.outcome !== 'ok' || !isRecord(response.result) || response.result.config_status !== 'valid') {
    const result = isRecord(response.result) ? response.result : {}
    throw new WebGovernanceError(`Governance configuration is not valid: ${String(result.config_status ?? response.outcome ?? 'unknown')}`)
  }
}

function verifiedResolution(response: Record<string, unknown>, expectedLocator: string): Record<string, unknown> {
  if (response.outcome !== 'ok' || !isRecord(response.result)) {
    throw new WebGovernanceError(`Governance resolution did not complete: ${String(response.outcome || 'unknown')}`)
  }
  const result = response.result
  if (result.config_status !== 'valid' || result.scope_status !== 'governed_single') {
    throw new WebGovernanceError(`Governance resolution is not verified: config=${String(result.config_status)} scope=${String(result.scope_status)}`)
  }
  if (!Array.isArray(result.object_resolutions) || result.object_resolutions.length !== 1) {
    throw new WebGovernanceError('Governance resolution must contain exactly one requested worktree')
  }
  const resolution = result.object_resolutions[0]
  if (!isRecord(resolution)
    || resolution.status !== 'governed'
    || typeof resolution.governed_project_id !== 'string'
    || !resolution.governed_project_id
    || typeof resolution.git_worktree_root !== 'string'
    || !path.isAbsolute(resolution.git_worktree_root)
    || typeof resolution.git_common_dir !== 'string'
    || !path.isAbsolute(resolution.git_common_dir)) {
    throw new WebGovernanceError('Governance resolution did not verify the requested worktree identity')
  }
  const worktree = normalizedExistingPath(resolution.git_worktree_root)
  const relative = path.relative(worktree, normalizedExistingPath(expectedLocator))
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new WebGovernanceError('Resolved locator is outside the verified Git worktree')
  }
  return resolution
}

/** The sole Web→Helper boundary: resolve a current, single governed worktree. */
export async function resolveCurrentWebProject(): Promise<WebGovernedProject> {
  const locator = configuredLocator()
  const resolution = verifiedResolution(await invokeGovernanceScope(locator, configuredWorkspaceRoot()), locator)
  return {
    id: String(resolution.governed_project_id),
    path: path.resolve(String(resolution.git_worktree_root)),
    gitCommonDir: path.resolve(String(resolution.git_common_dir)),
  }
}

/** The only project discovery path available to Web file browsing. */
export async function resolveWebGovernedProjects(): Promise<WebGovernedProject[]> {
  const locator = configuredLocator()
  const current = verifiedResolution(await invokeGovernanceScope(locator, configuredWorkspaceRoot()), locator)
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
  identities.set(String(current.governed_project_id), {
    project_id: String(current.governed_project_id),
    git_worktree_root: String(current.git_worktree_root),
    git_common_dir: String(current.git_common_dir),
  })
  return [...identities.values()]
    .sort((left, right) => left.project_id.localeCompare(right.project_id))
    .map((identity) => ({
      id: identity.project_id,
      path: path.resolve(identity.git_worktree_root),
      gitCommonDir: path.resolve(identity.git_common_dir),
    }))
}
