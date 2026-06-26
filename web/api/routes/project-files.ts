/**
 * Project files API：管辖项目文件浏览、Markdown/文本读取和 Git 工作区 diff。
 * 所有接口均为只读能力，不提供暂存、提交、还原或删除。
 */

import { execFile } from 'child_process'
import { Router, type Request, type Response } from 'express'
import { existsSync } from 'fs'
import { lstat, readdir, readFile, stat } from 'fs/promises'
import path from 'path'
import yaml from 'js-yaml'
import { parseCommitMessage, splitCommitMessage } from '../services/git.js'
import { LDVH_WORKSPACE_ROOT } from '../services/pytools.js'

const router = Router()

const GOVERNED_CONFIG = path.join(LDVH_WORKSPACE_ROOT, 'LDVH-GOVERNED-PROJECTS.yaml')
const MAX_FILE_BYTES = 300 * 1024
const MAX_DIRECTORY_ENTRIES = 500
const TEXT_SAMPLE_BYTES = 8192
const EXCLUDED_DIRS = new Set([
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

type GovernedProject = {
  id: string
  name: string
  description: string
  path: string
}

type FileKind = 'directory' | 'markdown' | 'yaml' | 'svg' | 'text' | 'binary'

function isValidCommitHash(hash: string): boolean {
  return /^[0-9a-f]{7,40}$/i.test(hash)
}

function runCommand(command: string, args: string[], cwd: string): Promise<string> {
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

function isInside(basePath: string, targetPath: string): boolean {
  const relative = path.relative(basePath, targetPath)
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))
}

function normalizeProjectPath(rawPath: unknown): string {
  const value = String(rawPath || '').trim()
  if (!value) return LDVH_WORKSPACE_ROOT
  return path.resolve(path.isAbsolute(value) ? value : path.join(LDVH_WORKSPACE_ROOT, value))
}

async function loadProjects(): Promise<GovernedProject[]> {
  if (!existsSync(GOVERNED_CONFIG)) {
    return [{
      id: 'workspace',
      name: 'Workspace',
      description: 'Current LDVH workspace',
      path: LDVH_WORKSPACE_ROOT,
    }]
  }

  const content = await readFile(GOVERNED_CONFIG, 'utf-8')
  const config = yaml.load(content) as { projects?: Array<Record<string, unknown>> } | null
  const projects = Array.isArray(config?.projects) ? config.projects : []

  return projects
    .map((project) => {
      const id = String(project.id || '').trim()
      const projectPath = normalizeProjectPath(project.path)
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

async function getProject(projectId: string): Promise<GovernedProject | null> {
  const projects = await loadProjects()
  return projects.find((project) => project.id === projectId) ?? null
}

function resolveProjectTarget(project: GovernedProject, relativePath: string): string | null {
  if (relativePath.includes('\0')) return null
  const projectRoot = path.resolve(project.path)
  const target = path.resolve(projectRoot, relativePath || '.')
  return isInside(projectRoot, target) ? target : null
}

function toProjectRelative(project: GovernedProject, absolutePath: string): string {
  const relative = path.relative(path.resolve(project.path), absolutePath)
  return relative === '' ? '' : relative.split(path.sep).join('/')
}

function detectKind(name: string, isDirectory: boolean, sample?: Buffer): FileKind {
  if (isDirectory) return 'directory'
  if (/\.(md|markdown)$/i.test(name)) return 'markdown'
  if (/\.(ya?ml)$/i.test(name)) return 'yaml'
  if (/\.svg$/i.test(name)) return 'svg'
  if (sample?.includes(0)) return 'binary'
  if (/\.(txt|json|ts|tsx|js|jsx|css|html|py|sh|toml|lock|gitignore|env|csv|xml)$/i.test(name)) return 'text'
  return sample?.includes(0) ? 'binary' : 'text'
}

function isHiddenPath(relativePath: string): boolean {
  return relativePath.split('/').some((part) => part.startsWith('.') && part.length > 1)
}

function parseGitStatusLine(project: GovernedProject, line: string) {
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

function parseCommitFileLine(project: GovernedProject, line: string) {
  const [status = '', ...pathParts] = line.split('\t')
  const filePath = pathParts[pathParts.length - 1] || ''
  return {
    status,
    path: filePath,
    absolutePath: path.join(project.path, filePath),
  }
}

router.get('/projects', async (_req: Request, res: Response): Promise<void> => {
  try {
    const projects = await loadProjects()
    res.json({
      ok: true,
      workspaceRoot: LDVH_WORKSPACE_ROOT,
      projects: projects.map((project) => ({
        ...project,
        docsPath: path.join(project.path, 'docs'),
        ldvhBasePath: path.join(project.path, 'ldvh-base'),
      })),
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to load governed projects'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/entries', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const dir = String(req.query.dir || '')
    const showHidden = String(req.query.showHidden || '') === 'true'
    const project = await getProject(projectId)
    if (!project) {
      res.status(404).json({ ok: false, error: 'Project not found' })
      return
    }

    const target = resolveProjectTarget(project, dir)
    if (!target) {
      res.status(403).json({ ok: false, error: 'Invalid directory path' })
      return
    }

    const targetStat = await lstat(target)
    if (!targetStat.isDirectory()) {
      res.status(400).json({ ok: false, error: 'Path is not a directory' })
      return
    }

    const rawEntries = await readdir(target, { withFileTypes: true })
    const visibleEntries = rawEntries
      .filter((entry) => !EXCLUDED_DIRS.has(entry.name))
      .filter((entry) => showHidden || !entry.name.startsWith('.'))
    const entries = await Promise.all(
      visibleEntries
        .slice(0, MAX_DIRECTORY_ENTRIES)
        .map(async (entry) => {
          const absolutePath = path.join(target, entry.name)
          const entryStat = await lstat(absolutePath)
          const isDirectory = entry.isDirectory()
          return {
            name: entry.name,
            path: toProjectRelative(project, absolutePath),
            absolutePath,
            type: isDirectory ? 'directory' : 'file',
            kind: detectKind(entry.name, isDirectory),
            size: entryStat.size,
            updated: entryStat.mtime.toISOString(),
          }
        }),
    )

    entries.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'directory' ? -1 : 1
      return a.name.localeCompare(b.name)
    })

    res.json({
      ok: true,
      project,
      dir: toProjectRelative(project, target),
      parent: toProjectRelative(project, target) ? toProjectRelative(project, path.dirname(target)) : '',
      showHidden,
      truncated: visibleEntries.length > MAX_DIRECTORY_ENTRIES,
      entries,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to list directory'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/content', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const filePath = String(req.query.path || '')
    const showHidden = String(req.query.showHidden || '') === 'true'
    const project = await getProject(projectId)
    if (!project) {
      res.status(404).json({ ok: false, error: 'Project not found' })
      return
    }

    const target = resolveProjectTarget(project, filePath)
    if (!target) {
      res.status(403).json({ ok: false, error: 'Invalid file path' })
      return
    }

    const relativePath = toProjectRelative(project, target)
    if (!showHidden && isHiddenPath(relativePath)) {
      res.status(403).json({ ok: false, error: 'Hidden file is not visible' })
      return
    }

    const fileStat = await stat(target)
    if (!fileStat.isFile()) {
      res.status(400).json({ ok: false, error: 'Path is not a file' })
      return
    }

    const sample = await readFile(target, { flag: 'r' }).then((buffer) => buffer.subarray(0, TEXT_SAMPLE_BYTES))
    const kind = detectKind(path.basename(target), false, sample)
    if (kind === 'binary') {
      res.json({
        ok: true,
        project,
        path: relativePath,
        absolutePath: target,
        kind,
        size: fileStat.size,
        content: '',
        truncated: false,
      })
      return
    }

    const buffer = await readFile(target)
    const truncated = buffer.length > MAX_FILE_BYTES
    res.json({
      ok: true,
      project,
      path: relativePath,
      absolutePath: target,
      kind,
      size: fileStat.size,
      content: buffer.subarray(0, MAX_FILE_BYTES).toString('utf-8'),
      truncated,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to read file'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/git/status', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const projects = projectId ? [await getProject(projectId)] : await loadProjects()
    const entries = []

    for (const project of projects) {
      if (!project) continue
      try {
        await runCommand('git', ['rev-parse', '--is-inside-work-tree'], project.path)
        const stdout = await runCommand('git', ['status', '--short', '--untracked-files=all'], project.path)
        for (const line of stdout.split('\n').filter(Boolean)) {
          entries.push(parseGitStatusLine(project, line))
        }
      } catch {
        // 非 Git 管辖项目不阻塞其它项目。
      }
    }

    res.json({ ok: true, entries })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to read git status'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/git/diff', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const filePath = String(req.query.path || '')
    const statusCode = String(req.query.status || '')
    const project = await getProject(projectId)
    if (!project) {
      res.status(404).json({ ok: false, error: 'Project not found' })
      return
    }

    const target = resolveProjectTarget(project, filePath)
    if (!target) {
      res.status(403).json({ ok: false, error: 'Invalid file path' })
      return
    }

    const relativePath = toProjectRelative(project, target)
    let diff = ''

    if (statusCode === '??') {
      const fileStat = await stat(target)
      if (!fileStat.isFile()) {
        res.status(400).json({ ok: false, error: 'Path is not a file' })
        return
      }
      const buffer = await readFile(target)
      if (buffer.subarray(0, TEXT_SAMPLE_BYTES).includes(0)) {
        diff = `Untracked binary file: ${relativePath}`
      } else {
        const truncated = buffer.length > MAX_FILE_BYTES
        const content = buffer.subarray(0, MAX_FILE_BYTES).toString('utf-8')
        diff = [
          `Untracked file: ${relativePath}`,
          truncated ? `Content truncated at ${MAX_FILE_BYTES} bytes.` : '',
          '',
          ...content.split('\n').map((line) => `+${line}`),
        ].filter((line, index) => line || index !== 1).join('\n')
      }
    } else {
      const unstaged = await runCommand('git', ['diff', '--', relativePath], project.path).catch(() => '')
      const staged = await runCommand('git', ['diff', '--cached', '--', relativePath], project.path).catch(() => '')
      diff = [staged && '## Staged changes', staged, unstaged && '## Unstaged changes', unstaged]
        .filter(Boolean)
        .join('\n\n')
    }

    res.json({
      ok: true,
      project,
      path: relativePath,
      absolutePath: target,
      status: statusCode,
      diff: diff || `No diff available for ${relativePath}`,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to read git diff'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/git/commits', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const count = Math.min(Math.max(parseInt(String(req.query.count || '50'), 10) || 50, 1), 200)
    const project = await getProject(projectId)
    if (!project) {
      res.status(404).json({ ok: false, error: 'Project not found' })
      return
    }

    await runCommand('git', ['rev-parse', '--is-inside-work-tree'], project.path)
    const stdout = await runCommand(
      'git',
      ['log', `-${count}`, '--date=iso-strict', '--format=%H%x1f%h%x1f%P%x1f%an%x1f%ai%x1f%B%x1e'],
      project.path,
    )
    const entries = stdout
      .trim()
      .split('\x1e')
      .map((block) => block.trim())
      .filter(Boolean)
      .map((block) => {
        const [hash, shortHash, parentsRaw, author, date, fullMessage = ''] = block.split('\x1f')
        const parents = parentsRaw ? parentsRaw.split(' ').filter(Boolean) : []
        const { subject: message, body } = splitCommitMessage(fullMessage)
        const { category, scope, description, isBreaking } = parseCommitMessage(message)
        return {
          hash,
          shortHash,
          parents,
          author,
          date,
          message,
          body,
          category,
          scope,
          description,
          isBreaking,
          isMerge: parents.length > 1,
        }
      })

    res.json({ ok: true, project, entries })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to read git commits'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/git/commit/:hash', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const { hash } = req.params
    const project = await getProject(projectId)
    if (!project) {
      res.status(404).json({ ok: false, error: 'Project not found' })
      return
    }
    if (!isValidCommitHash(hash)) {
      res.status(400).json({ ok: false, error: 'Invalid hash format' })
      return
    }

    await runCommand('git', ['rev-parse', '--is-inside-work-tree'], project.path)
    const meta = await runCommand('git', ['show', '-s', '--date=iso-strict', '--format=%H%n%h%n%P%n%an%n%ai%n%B', hash], project.path)
    const [fullHash = hash, shortHash = hash.slice(0, 7), parentsRaw = '', author = '', date = '', ...messageLines] = meta.split('\n')
    const fullMessage = messageLines.join('\n').trim()
    const { subject: message, body } = splitCommitMessage(fullMessage)
    const { category, scope, description, isBreaking } = parseCommitMessage(message)
    const filesStdout = await runCommand('git', ['show', '--name-status', '--format=', '--find-renames', '--root', hash], project.path)
    const files = filesStdout
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => parseCommitFileLine(project, line))
      .filter((file) => Boolean(file.path))

    const parents = parentsRaw ? parentsRaw.split(' ').filter(Boolean) : []
    res.json({
      ok: true,
      project,
      commit: {
        hash: fullHash,
        shortHash,
        parents,
        author,
        date,
        message,
        body,
        category,
        scope,
        description,
        isBreaking,
        isMerge: parents.length > 1,
        files,
      },
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to read git commit'
    res.status(500).json({ ok: false, error: message })
  }
})

router.get('/git/commit/:hash/diff', async (req: Request, res: Response): Promise<void> => {
  try {
    const projectId = String(req.query.projectId || '')
    const filePath = String(req.query.path || '')
    const { hash } = req.params
    const project = await getProject(projectId)
    if (!project) {
      res.status(404).json({ ok: false, error: 'Project not found' })
      return
    }
    if (!isValidCommitHash(hash)) {
      res.status(400).json({ ok: false, error: 'Invalid hash format' })
      return
    }

    const target = resolveProjectTarget(project, filePath)
    if (!target) {
      res.status(403).json({ ok: false, error: 'Invalid file path' })
      return
    }

    const relativePath = toProjectRelative(project, target)
    const diff = await runCommand('git', ['show', '--format=', '--find-renames', hash, '--', relativePath], project.path)
      .catch(() => '')

    res.json({
      ok: true,
      project,
      hash,
      path: relativePath,
      absolutePath: target,
      status: 'commit',
      diff: diff || `No diff available for ${relativePath} in ${hash}`,
    })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to read commit file diff'
    res.status(500).json({ ok: false, error: message })
  }
})

export default router
