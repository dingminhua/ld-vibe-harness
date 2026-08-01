/**
 * Web-owned field-level reader for current fact carriers.
 *
 * It deliberately does not call the Core validator: readable source fields,
 * field problems, and unconsumed source structure must remain distinguishable.
 */
import { existsSync } from 'node:fs'
import { readdir, readFile, stat } from 'node:fs/promises'
import path from 'node:path'
import yaml from 'js-yaml'
import { FACT_FIELD_CONTRACT, type FactType, type FieldExpectation } from './factFieldContract.js'

export const FACT_TYPE_DIRS = {
  workcase: 'workcases',
  adr: 'adrs',
  pitfall: 'pitfalls',
  spark: 'sparks',
  study: 'studies',
  'file-asset': 'file-assets',
} as const

export const FACT_TYPE_CARRIERS = {
  workcase: '.yaml',
  adr: '.yaml',
  pitfall: '.yaml',
  spark: '.yaml',
  study: '.md',
  'file-asset': '',
} as const

export type LocalFactType = FactType
export type LocalFactCarrier = 'yaml' | 'markdown' | 'directory'
export type LocalFactReadStatus = 'readable' | 'unreadable'

export type LocalFactIssue = {
  code: 'read_failed' | 'yaml_parse_failed' | 'frontmatter_missing' | 'frontmatter_unclosed' | 'frontmatter_parse_failed' | 'unexpected_fact_carrier'
  message: string
  path?: string
}

export type FieldIssue = {
  path: string
  reason: 'missing' | 'type_mismatch' | 'identity_mismatch'
  expected: string
  raw_value?: unknown
}

export type UnparsedStructure = {
  path: string
  reason: 'unconsumed_field' | 'unparseable_member'
  raw_value?: unknown
}

export type LocalFactMetadata = {
  object_ref: {
    governed_project_id: string
    fact_type_key: string
    object_id: string
  }
  canonical_path: string
  absolute_path: string
  carrier: LocalFactCarrier
}

export type LocalFactItem = LocalFactMetadata & {
  read_status: LocalFactReadStatus
  fact_object: Record<string, unknown> | null
  field_issues: FieldIssue[]
  unparsed_structures: UnparsedStructure[]
  issues: LocalFactIssue[]
}

export type LocalFactList = {
  status: 'complete' | 'type_not_integrated'
  items: LocalFactItem[]
  issues: LocalFactIssue[]
}

export interface LocalFactScope {
  worktreeLocator: string
  governedProjectId: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function baseDirOf(scope: LocalFactScope, type: LocalFactType): string {
  return path.join(scope.worktreeLocator, 'ldvh-base', FACT_TYPE_DIRS[type])
}

function expectedFileName(type: LocalFactType, objectId: string): string {
  return `${objectId}${FACT_TYPE_CARRIERS[type]}`
}

function carrierFor(type: LocalFactType): LocalFactCarrier {
  if (type === 'file-asset') return 'directory'
  return type === 'study' ? 'markdown' : 'yaml'
}

function metadataFor(scope: LocalFactScope, type: LocalFactType, objectId: string): LocalFactMetadata {
  const fileName = expectedFileName(type, objectId)
  return {
    object_ref: { governed_project_id: scope.governedProjectId, fact_type_key: type, object_id: objectId },
    canonical_path: path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], fileName),
    absolute_path: path.join(baseDirOf(scope, type), fileName),
    carrier: carrierFor(type),
  }
}

function isExpectedCarrierName(type: LocalFactType, fileName: string): boolean {
  if (type === 'file-asset') return /^file-asset-\d{4,}$/.test(fileName)
  const extension = FACT_TYPE_CARRIERS[type].replace('.', '\\.')
  return new RegExp(`^${type}-\\d{4,}${extension}$`).test(fileName)
}

function expectedManifestPath(metadata: LocalFactMetadata): string {
  return metadata.carrier === 'directory'
    ? path.join(metadata.absolute_path, 'file-asset.yaml')
    : metadata.absolute_path
}

function looksLikeFactCarrier(fileName: string): boolean {
  return /\.(?:yaml|yml|md)$/i.test(fileName)
}

function parseMarkdownWithFrontmatter(content: string): { metadata: Record<string, unknown> | null; body: string; issues: LocalFactIssue[] } {
  const lines = content.split(/\r?\n/)
  if (lines[0]?.trim() !== '---') {
    return { metadata: null, body: '', issues: [{ code: 'frontmatter_missing', message: 'Markdown 缺少 frontmatter' }] }
  }
  const end = lines.findIndex((line, index) => index > 0 && line.trim() === '---')
  if (end === -1) {
    return { metadata: null, body: '', issues: [{ code: 'frontmatter_unclosed', message: 'frontmatter 未闭合' }] }
  }
  try {
    const value = yaml.load(lines.slice(1, end).join('\n'))
    if (!isRecord(value)) {
      return { metadata: null, body: '', issues: [{ code: 'frontmatter_parse_failed', message: 'frontmatter 顶层不是键值映射' }] }
    }
    return { metadata: value, body: lines.slice(end + 1).join('\n').replace(/^\s*\n/, ''), issues: [] }
  } catch (error) {
    return { metadata: null, body: '', issues: [{ code: 'frontmatter_parse_failed', message: `frontmatter YAML 解析失败：${error instanceof Error ? error.message : String(error)}` }] }
  }
}

function matchesExpectation(value: unknown, expected: FieldExpectation): boolean {
  if (expected === 'array') return Array.isArray(value)
  if (expected === 'object') return isRecord(value)
  return typeof value === expected
}

const RECORD_ARRAY_FIELDS: Partial<Record<LocalFactType, ReadonlySet<string>>> = {
  workcase: new Set([
    'success_criterion_definitions', 'success_criterion_results', 'work_items',
    'creation_reviews', 'result_reviews', 'residual_responsibilities', 'relations',
  ]),
  spark: new Set(['evolution', 'relations']),
}

function isConsumableRecordMember(type: LocalFactType, field: string, member: Record<string, unknown>): boolean {
  if (type !== 'spark' || field !== 'evolution') return true
  return typeof member.at === 'string' && member.at.trim().length > 0
    && typeof member.summary === 'string' && member.summary.trim().length > 0
}

function projectFields(type: LocalFactType, objectId: string, parsed: Record<string, unknown>, extra: Record<string, unknown>): Pick<LocalFactItem, 'fact_object' | 'field_issues' | 'unparsed_structures'> {
  const all = { ...parsed, ...extra }
  const expected = FACT_FIELD_CONTRACT[type]
  const factObject: Record<string, unknown> = {}
  const fieldIssues: FieldIssue[] = []
  const unparsedStructures: UnparsedStructure[] = []
  for (const [field, contract] of Object.entries(expected)) {
    const { expected: kind } = contract
    const value = all[field]
    if (value === undefined || value === null) {
      if (contract.required) fieldIssues.push({ path: field, reason: 'missing', expected: kind })
      continue
    }
    if (!matchesExpectation(value, kind)) {
      fieldIssues.push({ path: field, reason: 'type_mismatch', expected: kind, raw_value: value })
      continue
    }
    factObject[field] = value
    if (kind === 'array' && Array.isArray(value) && RECORD_ARRAY_FIELDS[type]?.has(field)) {
      value.forEach((member, index) => {
        if (!isRecord(member) || !isConsumableRecordMember(type, field, member)) {
          unparsedStructures.push({ path: `${field}[${index}]`, reason: 'unparseable_member', raw_value: member })
        }
      })
    }
  }
  if (typeof all.object_id === 'string' && all.object_id !== objectId) {
    fieldIssues.push({ path: 'object_id', reason: 'identity_mismatch', expected: objectId, raw_value: all.object_id })
  }
  if (typeof all.fact_type_key === 'string' && all.fact_type_key !== type) {
    fieldIssues.push({ path: 'fact_type_key', reason: 'identity_mismatch', expected: type, raw_value: all.fact_type_key })
  }
  unparsedStructures.push(...Object.entries(all)
    .filter(([field]) => !(field in expected))
    .map(([field, value]) => ({ path: field, reason: 'unconsumed_field' as const, raw_value: value })))
  return { fact_object: factObject, field_issues: fieldIssues, unparsed_structures: unparsedStructures }
}

function unreadable(metadata: LocalFactMetadata, issues: LocalFactIssue[]): LocalFactItem {
  return { ...metadata, read_status: 'unreadable', fact_object: null, field_issues: [], unparsed_structures: [], issues: issues.map((issue) => ({ ...issue, path: issue.path ?? metadata.canonical_path })) }
}

async function readItemFile(scope: LocalFactScope, type: LocalFactType, fileName: string): Promise<LocalFactItem> {
  const objectId = fileName.replace(/\.(yaml|yml|md)$/i, '')
  const metadata = metadataFor(scope, type, objectId)
  let content: string
  try {
    content = await readFile(expectedManifestPath(metadata), 'utf-8')
  } catch (error) {
    return unreadable(metadata, [{ code: 'read_failed', message: `文件读取失败：${error instanceof Error ? error.message : String(error)}` }])
  }
  if (metadata.carrier === 'markdown') {
    const parsed = parseMarkdownWithFrontmatter(content)
    if (parsed.metadata === null) return unreadable(metadata, parsed.issues)
    return { ...metadata, read_status: 'readable', ...projectFields(type, objectId, parsed.metadata, { report_body: parsed.body }), issues: [] }
  }
  let parsed: unknown
  try {
    parsed = yaml.load(content)
  } catch (error) {
    return unreadable(metadata, [{ code: 'yaml_parse_failed', message: `YAML 解析失败：${error instanceof Error ? error.message : String(error)}` }])
  }
  if (!isRecord(parsed)) {
    return unreadable(metadata, [{ code: 'yaml_parse_failed', message: 'YAML 顶层不是键值映射' }])
  }
  if (metadata.carrier === 'directory') {
    try {
      const members = await readdir(metadata.absolute_path, { withFileTypes: true })
      const expectedMembers = parsed.status === 'deleted'
        ? new Set(['file-asset.yaml'])
        : new Set(['file-asset.yaml', 'payload'])
      if (members.some((member) => !member.isFile() || !expectedMembers.has(member.name))
        || members.length !== expectedMembers.size) {
        return unreadable(metadata, [{ code: 'read_failed', message: 'FileAsset 目录成员不符合当前状态的正式 carrier 结构' }])
      }
    } catch (error) {
      return unreadable(metadata, [{ code: 'read_failed', message: `FileAsset 目录读取失败：${error instanceof Error ? error.message : String(error)}` }])
    }
  }
  return { ...metadata, read_status: 'readable', ...projectFields(type, objectId, parsed, {}), issues: [] }
}

function directoryStatus(scope: LocalFactScope, type: LocalFactType): LocalFactList | null {
  if (existsSync(baseDirOf(scope, type))) return null
  return { status: 'type_not_integrated', items: [], issues: [{ code: 'read_failed', message: `该类型尚未接入：缺少正式对象目录 ${path.posix.join('ldvh-base', FACT_TYPE_DIRS[type])}` }] }
}

export async function listLocalFacts(type: LocalFactType, scope: LocalFactScope): Promise<LocalFactList> {
  const missing = directoryStatus(scope, type)
  if (missing) return missing
  const entries = await readdir(baseDirOf(scope, type), { withFileTypes: true })
  const carriers = type === 'file-asset'
    ? entries.filter((entry) => entry.isDirectory())
    : entries.filter((entry) => entry.isFile() && looksLikeFactCarrier(entry.name))
  const fileNames = carriers.filter((entry) => isExpectedCarrierName(type, entry.name)).map((entry) => entry.name).sort((left, right) => left.localeCompare(right))
  const issues = carriers.filter((entry) => !isExpectedCarrierName(type, entry.name)).map((entry) => ({
    code: 'unexpected_fact_carrier' as const,
    message: `${type} 正式载体必须是 ${type}-NNNN${type === 'file-asset' ? ' 目录' : FACT_TYPE_CARRIERS[type]}，已忽略错载体 ${entry.name}`,
    path: path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], entry.name),
  }))
  return { status: 'complete', items: await Promise.all(fileNames.map((fileName) => readItemFile(scope, type, fileName))), issues }
}

export async function readLocalFact(type: LocalFactType, objectId: string, scope: LocalFactScope): Promise<{ status: 'ok'; item: LocalFactItem } | { status: 'not_found' | 'type_not_integrated'; metadata: LocalFactMetadata; issues: LocalFactIssue[] }> {
  const metadata = metadataFor(scope, type, objectId)
  const missing = directoryStatus(scope, type)
  if (missing) return { status: 'type_not_integrated', metadata, issues: missing.issues }
  const expectedName = expectedFileName(type, objectId)
  const filePath = path.join(baseDirOf(scope, type), expectedName)
  try {
    const statResult = await stat(filePath)
    if (type === 'file-asset' ? !statResult.isDirectory() : !statResult.isFile()) {
      return { status: 'not_found', metadata, issues: [{ code: 'read_failed', message: `未找到预期事实对象 ${expectedName}`, path: metadata.canonical_path }] }
    }
  } catch {
    return { status: 'not_found', metadata, issues: [{ code: 'read_failed', message: `未找到预期事实对象 ${expectedName}`, path: metadata.canonical_path }] }
  }
  return { status: 'ok', item: await readItemFile(scope, type, expectedName) }
}
