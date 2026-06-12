/**
 * Web-native fact source reader.
 *
 * This service reads Git-backed YAML fact objects directly for Human-facing
 * Web views. It is read-only and does not replace specs or Code validation.
 */

import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export const LDVH_ROOT = path.resolve(process.env.LDVH_ROOT || path.resolve(__dirname, '../../..'))
export const LDVH_BASE_DIR = path.join(LDVH_ROOT, 'ldvh-base')

export const OBJECT_TYPES = ['workarea', 'taskplan', 'task', 'subtask', 'adr', 'pitfall', 'memo'] as const
export type ObjectType = (typeof OBJECT_TYPES)[number]

const DIRECTORY_MAP: Record<ObjectType, string> = {
  workarea: 'workareas',
  taskplan: 'taskplans',
  task: 'tasks',
  subtask: 'subtasks',
  adr: 'adrs',
  pitfall: 'pitfalls',
  memo: 'memos',
}

const LIST_SUMMARY_FIELDS = ['category', 'priority', 'severity', 'repeatability'] as const

export interface WebFactResult {
  ok: boolean
  command: string
  action: string
  target: string
  summary: Record<string, unknown>
  issues: Array<Record<string, unknown>>
  data: Record<string, unknown>
}

export interface WebFactError {
  ok: false
  error: string
  stderr: string
  exitCode: number | string | null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function toStringValue(value: unknown, fallback = ''): string {
  if (value instanceof Date) return value.toISOString().slice(0, 10)
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return fallback
}

function objectDir(type: ObjectType, baseDir = LDVH_ROOT): string {
  return path.join(baseDir, 'ldvh-base', DIRECTORY_MAP[type])
}

function readYamlFile(filePath: string): Record<string, unknown> | null {
  try {
    const content = fs.readFileSync(filePath, 'utf-8')
    const data = yaml.load(content)
    return isRecord(data) ? data : null
  } catch {
    return null
  }
}

function listYamlFiles(type: ObjectType, baseDir = LDVH_ROOT): string[] {
  const dir = objectDir(type, baseDir)
  if (!fs.existsSync(dir)) return []

  return fs
    .readdirSync(dir)
    .filter((filename) => filename.endsWith('.yaml') || filename.endsWith('.yml'))
    .sort()
    .map((filename) => path.join(dir, filename))
}

function normalizeListItem(data: Record<string, unknown>, filePath: string, type: ObjectType): Record<string, unknown> | null {
  const id = toStringValue(data.id)
  if (!id) return null

  const item: Record<string, unknown> = {
    id,
    type: toStringValue(data.type, type),
    status: toStringValue(data.status, 'unknown'),
    title: toStringValue(data.title, id),
    path: filePath,
    updated: toStringValue(data.updated),
  }

  const titleEn = toStringValue(data.title_en)
  const titleZh = toStringValue(data.title_zh)
  if (titleEn) item.title_en = titleEn
  if (titleZh) item.title_zh = titleZh

  for (const field of LIST_SUMMARY_FIELDS) {
    const value = toStringValue(data[field])
    if (value) item[field] = value
  }

  return item
}

function makeResult(action: string, target: string, summary: Record<string, unknown>, data: Record<string, unknown>): WebFactResult {
  return {
    ok: true,
    command: 'web-facts',
    action,
    target,
    summary,
    issues: [],
    data,
  }
}

export async function listObjects(type: ObjectType, baseDir: string = LDVH_ROOT, status?: string): Promise<WebFactResult | WebFactError> {
  const files = listYamlFiles(type, baseDir)
  const items = files
    .map((filePath) => {
      const data = readYamlFile(filePath)
      return data ? normalizeListItem(data, filePath, type) : null
    })
    .filter((item): item is Record<string, unknown> => Boolean(item))
    .filter((item) => !status || item.status === status)
    .sort((a, b) => {
      const updatedDelta = toStringValue(b.updated).localeCompare(toStringValue(a.updated))
      if (updatedDelta !== 0) return updatedDelta
      return toStringValue(a.id).localeCompare(toStringValue(b.id))
    })

  return makeResult('list', type, { count: items.length }, { items })
}

export async function showObject(id: string, baseDir: string = LDVH_ROOT): Promise<WebFactResult | WebFactError> {
  for (const type of OBJECT_TYPES) {
    for (const filePath of listYamlFiles(type, baseDir)) {
      const data = readYamlFile(filePath)
      if (!data || data.id !== id) continue
      return makeResult('show', id, { id, type: toStringValue(data.type, type), status: toStringValue(data.status, 'unknown') }, { ...data, path: filePath })
    }
  }

  return {
    ok: false,
    error: `Object not found: ${id}`,
    stderr: '',
    exitCode: 1,
  }
}

export function readFactData(filePath: string): Record<string, unknown> {
  const resolvedPath = path.isAbsolute(filePath) ? filePath : path.join(LDVH_ROOT, filePath)
  return readYamlFile(resolvedPath) ?? {}
}
