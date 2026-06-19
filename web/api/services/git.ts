/**
 * Git 服务：通过子进程执行 git 命令获取提交日志
 */

import { execFile } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import { getRelativeTime as sharedGetRelativeTime } from './time.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/** LDVH 项目根目录 */
const LDVH_ROOT = process.env.LDVH_ROOT || path.resolve(__dirname, '../../..')

export interface GitLogEntry {
  hash: string
  shortHash: string
  author: string
  date: string
  message: string
  category: string
  scope: string
  description: string
  isBreaking: boolean
  relativeTime: string
}

/** Conventional commit 分类颜色 */
export const CATEGORY_COLORS: Record<string, string> = {
  feat: '#3b82f6',      // blue
  fix: '#ef4444',       // red
  docs: '#6b7280',      // gray
  style: '#a855f7',     // purple
  refactor: '#06b6d4',  // cyan
  test: '#eab308',      // yellow
  chore: '#6b7280',     // gray
  perf: '#22c55e',      // green
  ci: '#ec4899',        // pink
  build: '#92400e',     // brown
  default: '#6b7280',   // gray
}

/**
 * 解析 conventional commit message
 * 格式: type(scope)!: description、type!: description 或 type: description
 */
function parseCommitMessage(message: string): { category: string; scope: string; description: string; isBreaking: boolean } {
  const match = message.match(/^([A-Za-z]+)(?:\(([^)]+)\))?(!)?:\s+(.+)$/)
  if (match) {
    return {
      category: match[1].toLowerCase(),
      scope: match[2] ?? '',
      isBreaking: Boolean(match[3]),
      description: match[4],
    }
  }
  return {
    category: 'other',
    scope: '',
    description: message,
    isBreaking: false,
  }
}



/**
 * 获取 git log 列表
 */
export async function getGitLog(count: number = 50, locale: string = 'zh'): Promise<GitLogEntry[]> {
  return new Promise((resolve, reject) => {
    execFile(
      'git',
      ['log', `-${count}`, '--format=%H|%h|%an|%ai|%s'],
      { cwd: LDVH_ROOT, maxBuffer: 5 * 1024 * 1024 },
      (error, stdout) => {
        if (error) {
          reject(new Error(`git log failed: ${error.message}`))
          return
        }

        const lines = stdout.trim().split('\n').filter(Boolean)
        const entries: GitLogEntry[] = lines.map((line) => {
          const [hash, shortHash, author, date, ...msgParts] = line.split('|')
          const message = msgParts.join('|')
          const { category, scope, description, isBreaking } = parseCommitMessage(message)
          return {
            hash,
            shortHash,
            author,
            date,
            message,
            category,
            scope,
            description,
            isBreaking,
            relativeTime: sharedGetRelativeTime(date, locale),
          }
        })

        resolve(entries)
      },
    )
  })
}

/**
 * 获取指定 commit 的 show --stat 输出
 */
export async function getGitShow(hash: string): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      'git',
      ['show', '--stat', hash],
      { cwd: LDVH_ROOT, maxBuffer: 5 * 1024 * 1024 },
      (error, stdout) => {
        if (error) {
          reject(new Error(`git show failed: ${error.message}`))
          return
        }
        resolve(stdout)
      },
    )
  })
}
