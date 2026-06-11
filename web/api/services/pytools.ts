/**
 * PyTools 子进程服务：通过 python3 调用 LDVH CLI 工具获取事实模型数据
 */

import { execFile } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/** LDVH 项目根目录 */
export const LDVH_ROOT = process.env.LDVH_ROOT || path.resolve(__dirname, '../../..')

/** tools 目录 */
export const TOOLS_DIR = path.join(LDVH_ROOT, 'tools')

/** ldvh-base 目录 */
export const LDVH_BASE_DIR = path.join(LDVH_ROOT, 'ldvh-base')

/** 所有对象类型 */
export const OBJECT_TYPES = ['workarea', 'taskplan', 'task', 'subtask', 'adr', 'pitfall', 'memo'] as const
export type ObjectType = (typeof OBJECT_TYPES)[number]

export interface PyToolsResult {
  ok: boolean
  command: string
  action: string
  target: string
  summary: Record<string, unknown>
  issues: Array<Record<string, unknown>>
  data: Record<string, unknown>
}

export interface PyToolsError {
  ok: false
  error: string
  stderr: string
  exitCode: number | string | null
}

export type PyToolsJson = Record<string, unknown>

function parseJson(stdout: string): PyToolsJson | null {
  const trimmed = stdout.trim()
  if (!trimmed) return null

  try {
    const parsed = JSON.parse(trimmed)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as PyToolsJson
    }
    return { value: parsed } as PyToolsJson
  } catch {
    return null
  }
}

/**
 * 执行 PyTools CLI 工具并返回 JSON 结果
 */
export async function runPyTools(tool: string, args: string[]): Promise<PyToolsResult | PyToolsError> {
  const toolPath = path.join(TOOLS_DIR, tool)

  return new Promise((resolve) => {
    execFile('python3', [toolPath, ...args], { maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      const parsed = parseJson(stdout)
      if (parsed) {
        resolve(parsed as unknown as PyToolsResult)
        return
      }

      if (error) {
        resolve({
          ok: false,
          error: error.message,
          stderr: stderr?.trim() || '',
          exitCode: error.code ?? null,
        })
        return
      }

      try {
        const result = JSON.parse(stdout)
        resolve(result)
      } catch (parseError) {
        resolve({
          ok: false,
          error: `JSON parse failed: ${parseError instanceof Error ? parseError.message : String(parseError)}`,
          stderr: stderr?.trim() || '',
          exitCode: null,
        })
      }
    })
  })
}

/**
 * 执行 PyTools CLI 工具并返回原始 JSON 结果，允许非零退出码但要求 stdout 可解析
 */
export async function runPyToolsJson(tool: string, args: string[]): Promise<PyToolsJson | PyToolsError> {
  const toolPath = path.join(TOOLS_DIR, tool)

  return new Promise((resolve) => {
    execFile('python3', [toolPath, ...args], { maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      const parsed = parseJson(stdout)
      if (parsed) {
        resolve(parsed)
        return
      }

      if (error) {
        resolve({
          ok: false,
          error: error.message,
          stderr: stderr?.trim() || '',
          exitCode: error.code ?? null,
        })
        return
      }

      resolve({
        ok: false,
        error: 'JSON parse failed: empty or invalid stdout',
        stderr: stderr?.trim() || '',
        exitCode: null,
      })
    })
  })
}

/**
 * 列出指定类型的事实对象
 */
export async function listObjects(type: ObjectType, baseDir: string = LDVH_ROOT, status?: string): Promise<PyToolsResult | PyToolsError> {
  const args = ['list', type, '--format', 'json', '--base-dir', baseDir]
  if (status) {
    args.push('--status', status)
  }
  return runPyTools('fact_cli.py', args)
}

/**
 * 查看单个事实对象详情
 */
export async function showObject(id: string, baseDir: string = LDVH_ROOT): Promise<PyToolsResult | PyToolsError> {
  return runPyTools('fact_cli.py', ['show', id, '--format', 'json', '--base-dir', baseDir])
}

/**
 * 校验 ldvh-base 目录下所有事实对象
 */
export async function validate(baseDir: string = LDVH_BASE_DIR): Promise<PyToolsResult | PyToolsError> {
  return runPyToolsJson('fact_validate.py', [baseDir, '--format', 'json']) as Promise<PyToolsResult | PyToolsError>
}
