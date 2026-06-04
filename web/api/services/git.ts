/**
 * Git 服务：通过子进程执行 git 命令获取提交日志
 */

import { execFile } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'

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
}

/**
 * 获取 git log 列表
 */
export async function getGitLog(count: number = 50): Promise<GitLogEntry[]> {
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
          return {
            hash,
            shortHash,
            author,
            date,
            message: msgParts.join('|'),
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
