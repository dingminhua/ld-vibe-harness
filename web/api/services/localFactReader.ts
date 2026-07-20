/**
 * 本地事实对象直读服务（V4 五类统一读取路径）。
 *
 * Web 是只读呈现层：对 ldvh-base/<type>/ 下的 YAML / Markdown(frontmatter) 做
 * 机械映射，不 spawn Python、不做业务校验。读不出或缺失字段如实记录在 issues 中。
 */

import { existsSync } from 'node:fs'
import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import yaml from 'js-yaml'

export const FACT_TYPE_DIRS = {
  workcase: 'workcases',
  adr: 'adrs',
  pitfall: 'pitfalls',
  spark: 'sparks',
  study: 'studies',
} as const

export const FACT_TYPE_CARRIERS = {
  workcase: '.yaml',
  adr: '.yaml',
  pitfall: '.yaml',
  spark: '.yaml',
  study: '.md',
} as const

export type LocalFactType = keyof typeof FACT_TYPE_DIRS

export type LocalFactIssue = {
  code: string
  message: string
  path?: string
}

export type LocalFactItem = {
  object_ref: {
    governed_project_id: string
    fact_type_key: string
    object_id: string
  }
  canonical_path: string
  absolute_path: string
  check_status: 'unverified' | 'parse_failed'
  fact_object: Record<string, unknown>
  issues: LocalFactIssue[]
}

export type LocalFactList = {
  status: 'complete' | 'type_not_integrated'
  items: LocalFactItem[]
  issues: LocalFactIssue[]
}

export interface LocalFactScope {
  /** governed project 根目录（worktree locator），其下应有 ldvh-base/ */
  worktreeLocator: string
  governedProjectId: string
}

export function localFactScopeFromEnv(): LocalFactScope {
  return {
    worktreeLocator: process.env.LDVH_WEB_WORKTREE_LOCATOR || process.env.LDVH_ROOT || '',
    governedProjectId: process.env.LDVH_WEB_GOVERNED_PROJECT_ID || 'workspace',
  }
}

function baseDirOf(scope: LocalFactScope, type: LocalFactType): string {
  return path.join(scope.worktreeLocator, 'ldvh-base', FACT_TYPE_DIRS[type])
}

function expectedFileName(type: LocalFactType, objectId: string): string {
  return `${objectId}${FACT_TYPE_CARRIERS[type]}`
}

function isExpectedCarrierName(type: LocalFactType, fileName: string): boolean {
  const escapedType = type.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const escapedExtension = FACT_TYPE_CARRIERS[type].replace('.', '\\.')
  return new RegExp(`^${escapedType}-\\d{4,}${escapedExtension}$`).test(fileName)
}

function looksLikeFactCarrier(fileName: string): boolean {
  return /\.(?:yaml|yml|md)$/i.test(fileName)
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

/** 手写 frontmatter 解析：首个 `---` 与下一个 `---` 之间为 YAML 元数据，其后为 Markdown 正文。 */
function parseMarkdownWithFrontmatter(content: string): { metadata: Record<string, unknown>; body: string; issues: LocalFactIssue[] } {
  const issues: LocalFactIssue[] = []
  const lines = content.split(/\r?\n/)
  if (lines[0]?.trim() !== '---') {
    issues.push({ code: 'frontmatter_missing', message: 'Markdown 缺少 frontmatter，正文按全文呈现' })
    return { metadata: {}, body: content, issues }
  }
  let end = -1
  for (let index = 1; index < lines.length; index += 1) {
    if (lines[index].trim() === '---') {
      end = index
      break
    }
  }
  if (end === -1) {
    issues.push({ code: 'frontmatter_unclosed', message: 'frontmatter 未闭合，正文按全文呈现' })
    return { metadata: {}, body: content, issues }
  }
  const rawMeta = lines.slice(1, end).join('\n')
  let metadata: Record<string, unknown> = {}
  try {
    const parsed = yaml.load(rawMeta)
    if (isRecord(parsed)) {
      metadata = parsed
    } else if (parsed !== null && parsed !== undefined) {
      issues.push({ code: 'frontmatter_not_mapping', message: 'frontmatter 不是键值映射，已忽略' })
    }
  } catch (error) {
    issues.push({
      code: 'frontmatter_parse_failed',
      message: `frontmatter YAML 解析失败：${error instanceof Error ? error.message : String(error)}`,
    })
  }
  const body = lines.slice(end + 1).join('\n').replace(/^\s*\n/, '')
  return { metadata, body, issues }
}

const REQUIRED_FIELDS = ['object_id', 'fact_type_key'] as const

function toItem(
  scope: LocalFactScope,
  type: LocalFactType,
  fileName: string,
  parsed: Record<string, unknown>,
  extraFields: Record<string, unknown>,
  parseIssues: LocalFactIssue[],
): LocalFactItem {
  const absolutePath = path.join(baseDirOf(scope, type), fileName)
  const canonicalPath = path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], fileName)
  const issues: LocalFactIssue[] = parseIssues.map((issue) => ({ ...issue, path: canonicalPath }))

  const factObject: Record<string, unknown> = { ...parsed, ...extraFields }
  for (const field of REQUIRED_FIELDS) {
    if (typeof factObject[field] !== 'string' || !factObject[field]) {
      issues.push({ code: 'field_missing', message: `缺失必需字段：${field}`, path: canonicalPath })
    }
  }
  const objectId = typeof factObject.object_id === 'string' && factObject.object_id
    ? factObject.object_id
    : fileName.replace(/\.(yaml|yml|md)$/i, '')
  const factTypeKey = typeof factObject.fact_type_key === 'string' && factObject.fact_type_key
    ? factObject.fact_type_key
    : type

  const failed = parseIssues.some((issue) => issue.code.endsWith('parse_failed'))
  return {
    object_ref: {
      governed_project_id: scope.governedProjectId,
      fact_type_key: factTypeKey,
      object_id: objectId,
    },
    canonical_path: canonicalPath,
    absolute_path: absolutePath,
    check_status: failed ? 'parse_failed' : 'unverified',
    fact_object: factObject,
    issues,
  }
}

async function readItemFile(scope: LocalFactScope, type: LocalFactType, fileName: string): Promise<LocalFactItem> {
  const absolutePath = path.join(baseDirOf(scope, type), fileName)
  const canonicalPath = path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], fileName)
  let content: string
  try {
    content = await readFile(absolutePath, 'utf-8')
  } catch (error) {
    return toItem(scope, type, fileName, {}, {}, [{
      code: 'read_failed',
      message: `文件读取失败：${error instanceof Error ? error.message : String(error)}`,
      path: canonicalPath,
    }])
  }

  if (/\.md$/i.test(fileName)) {
    const { metadata, body, issues } = parseMarkdownWithFrontmatter(content)
    return toItem(scope, type, fileName, metadata, { report_body: body }, issues)
  }

  try {
    const parsed = yaml.load(content)
    if (!isRecord(parsed)) {
      return toItem(scope, type, fileName, {}, {}, [{
        code: 'yaml_not_mapping',
        message: 'YAML 顶层不是键值映射',
        path: canonicalPath,
      }])
    }
    return toItem(scope, type, fileName, parsed, {}, [])
  } catch (error) {
    return toItem(scope, type, fileName, {}, {}, [{
      code: 'yaml_parse_failed',
      message: `YAML 解析失败：${error instanceof Error ? error.message : String(error)}`,
      path: canonicalPath,
    }])
  }
}

function directoryStatus(scope: LocalFactScope, type: LocalFactType): LocalFactList | null {
  const dir = baseDirOf(scope, type)
  if (existsSync(dir)) return null
  return {
    status: 'type_not_integrated',
    items: [],
    issues: [{
      code: 'type_not_integrated',
      message: `该类型尚未接入：缺少正式对象目录 ${path.posix.join('ldvh-base', FACT_TYPE_DIRS[type])}`,
    }],
  }
}

/** 列出某类型的全部事实对象；目录不存在时返回独立的 type_not_integrated。 */
export async function listLocalFacts(type: LocalFactType, scope: LocalFactScope = localFactScopeFromEnv()): Promise<LocalFactList> {
  const missing = directoryStatus(scope, type)
  if (missing) return missing

  const dir = baseDirOf(scope, type)
  const entries = await readdir(dir, { withFileTypes: true })
  const carrierEntries = entries.filter((entry) => entry.isFile() && looksLikeFactCarrier(entry.name))
  const fileNames = carrierEntries
    .filter((entry) => isExpectedCarrierName(type, entry.name))
    .map((entry) => entry.name)
    .sort((left, right) => left.localeCompare(right))

  const carrierIssues = carrierEntries
    .filter((entry) => !isExpectedCarrierName(type, entry.name))
    .map((entry) => ({
      code: 'unexpected_fact_carrier',
      message: `${type} 正式载体必须是 ${type}-NNNN${FACT_TYPE_CARRIERS[type]}，已忽略错载体 ${entry.name}`,
      path: path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], entry.name),
    }))

  const items = await Promise.all(fileNames.map((fileName) => readItemFile(scope, type, fileName)))
  return { status: 'complete', items, issues: carrierIssues }
}

/** 按 object_id 直读单个事实对象文件；找不到返回 null，目录缺失原样上报。 */
export async function readLocalFact(
  type: LocalFactType,
  objectId: string,
  scope: LocalFactScope = localFactScopeFromEnv(),
): Promise<
  | { status: 'ok'; item: LocalFactItem }
  | { status: 'not_found' }
  | { status: 'type_not_integrated'; issues: LocalFactIssue[] }
  | { status: 'unavailable'; issues: LocalFactIssue[] }
> {
  const missing = directoryStatus(scope, type)
  if (missing) return { status: 'type_not_integrated', issues: missing.issues }

  const dir = baseDirOf(scope, type)
  const entries = await readdir(dir, { withFileTypes: true })
  const expectedName = expectedFileName(type, objectId)
  if (entries.some((entry) => entry.isFile() && entry.name === expectedName)) {
    return { status: 'ok', item: await readItemFile(scope, type, expectedName) }
  }
  const wrongCarrier = entries.find((entry) =>
    entry.isFile()
    && looksLikeFactCarrier(entry.name)
    && entry.name.replace(/\.(yaml|yml|md)$/i, '') === objectId,
  )
  if (wrongCarrier) {
    return {
      status: 'unavailable',
      issues: [{
        code: 'unexpected_fact_carrier',
        message: `${objectId} 使用了错载体 ${wrongCarrier.name}；${type} 必须使用 ${expectedName}`,
        path: path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], wrongCarrier.name),
      }],
    }
  }
  return { status: 'not_found' }
}
