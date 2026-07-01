import { execFile } from 'child_process'
import { existsSync } from 'fs'
import { readFile } from 'fs/promises'
import path from 'path'
import yaml from 'js-yaml'
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

const GOVERNED_CONFIG_CANDIDATES = [
  path.join(LDVH_ROOT, 'LDVH-GOVERNED-PROJECTS.yaml'),
  path.join(LDVH_WORKSPACE_ROOT, 'LDVH-GOVERNED-PROJECTS.yaml'),
]

export type GovernedProject = {
  id: string
  name: string
  description: string
  path: string
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
  const governedConfig = GOVERNED_CONFIG_CANDIDATES.find((candidate) => existsSync(candidate))
  if (!governedConfig) {
    return [{
      id: 'workspace',
      name: 'Workspace',
      description: 'Current LDVH workspace',
      path: LDVH_ROOT,
    }]
  }

  const content = await readFile(governedConfig, 'utf-8')
  const config = yaml.load(content) as { projects?: Array<Record<string, unknown>> } | null
  const projects = Array.isArray(config?.projects) ? config.projects : []

  return projects
    .map((project) => {
      const id = String(project.id || '').trim()
      const projectPath = normalizeProjectPath(project.path, path.dirname(governedConfig))
      if (!id || !projectPath) return null
      return {
        id,
        name: String(project.name || id),
        description: String(project.description || ''),
        path: projectPath,
      }
    })
    .filter((project): project is GovernedProject => Boolean(project))
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
