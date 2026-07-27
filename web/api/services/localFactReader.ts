/**
 * Web-owned field-level reader for current fact carriers.
 *
 * It deliberately does not call the Core validator: readable source fields,
 * field problems, and unconsumed source structure must remain distinguishable.
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
export type LocalFactCarrier = 'yaml' | 'markdown'
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

type FieldExpectation = 'string' | 'number' | 'array' | 'object'

const COMMON_FIELDS: Record<string, FieldExpectation> = {
  object_id: 'string', fact_type_key: 'string', title: 'string', status: 'string',
  created_at: 'string', updated_at: 'string', urls: 'array', relations: 'array',
}

const REQUIRED_FIELDS: Record<LocalFactType, ReadonlySet<string>> = {
  workcase: new Set(['object_id', 'fact_type_key', 'title', 'status', 'created_at', 'updated_at']),
  adr: new Set(['object_id', 'fact_type_key', 'title', 'status', 'created_at', 'updated_at']),
  pitfall: new Set(['object_id', 'fact_type_key', 'title', 'status', 'created_at', 'updated_at']),
  spark: new Set(['object_id', 'fact_type_key', 'title', 'status', 'created_at', 'updated_at', 'summary']),
  study: new Set(['object_id', 'fact_type_key', 'title', 'status', 'created_at', 'updated_at']),
}

/**
 * Page-consumed field names only. Their semantics, requiredness, and titles
 * remain in the current field registry and type specifications.
 */
const DETAIL_FIELDS: Record<LocalFactType, Record<string, FieldExpectation>> = {
  workcase: {
    goal: 'string', scope: 'string', phase: 'string', summary: 'string', resume_from: 'string',
    waiting_on: 'string', blocking_summary: 'string', priority: 'string',
    success_criterion_definitions: 'array', success_criterion_results: 'array', plan_version: 'number',
    work_items: 'array', creation_reviews: 'array', execution_approval: 'object', result_version: 'number',
    result_summary: 'string', controller_check_summary: 'string', result_reviews: 'array',
    validation_summary: 'string', closure_proposal: 'object', closure_outcome: 'string',
    disposition_summary: 'string', residual_responsibilities: 'array',
  },
  adr: {
    decision_question: 'string', decision: 'string', applicability: 'string', rationale: 'string',
    consequences: 'string', disposition_summary: 'string',
  },
  pitfall: {
    symptoms: 'string', trigger_conditions: 'string', applicability: 'string', validation_summary: 'string',
    root_cause: 'string', resolution: 'string', avoidance: 'string', disposition_summary: 'string', tags: 'array',
  },
  spark: {
    intent: 'string', summary: 'string', evolution: 'array', disposition_summary: 'string', priority: 'string',
  },
  study: {
    research_intent: 'string', research_question: 'string', abstract: 'string',
    recommendation_summary: 'string', report_body: 'string', disposition_summary: 'string',
  },
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
  const extension = FACT_TYPE_CARRIERS[type].replace('.', '\\.')
  return new RegExp(`^${type}-\\d{4,}${extension}$`).test(fileName)
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

function projectFields(type: LocalFactType, objectId: string, parsed: Record<string, unknown>, extra: Record<string, unknown>): Pick<LocalFactItem, 'fact_object' | 'field_issues' | 'unparsed_structures'> {
  const all = { ...parsed, ...extra }
  const expected = { ...COMMON_FIELDS, ...DETAIL_FIELDS[type] }
  const factObject: Record<string, unknown> = {}
  const fieldIssues: FieldIssue[] = []
  const unparsedStructures: UnparsedStructure[] = []
  for (const [field, kind] of Object.entries(expected)) {
    const value = all[field]
    if (value === undefined || value === null) {
      if (REQUIRED_FIELDS[type].has(field)) fieldIssues.push({ path: field, reason: 'missing', expected: kind })
      continue
    }
    if (!matchesExpectation(value, kind)) {
      fieldIssues.push({ path: field, reason: 'type_mismatch', expected: kind, raw_value: value })
      continue
    }
    factObject[field] = value
    if (kind === 'array' && Array.isArray(value) && RECORD_ARRAY_FIELDS[type]?.has(field)) {
      value.forEach((member, index) => {
        if (!isRecord(member)) {
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
    content = await readFile(metadata.absolute_path, 'utf-8')
  } catch (error) {
    return unreadable(metadata, [{ code: 'read_failed', message: `文件读取失败：${error instanceof Error ? error.message : String(error)}` }])
  }
  if (metadata.carrier === 'markdown') {
    const parsed = parseMarkdownWithFrontmatter(content)
    if (parsed.metadata === null) return unreadable(metadata, parsed.issues)
    return { ...metadata, read_status: 'readable', ...projectFields(type, objectId, parsed.metadata, { report_body: parsed.body }), issues: [] }
  }
  try {
    const parsed = yaml.load(content)
    if (!isRecord(parsed)) {
      return unreadable(metadata, [{ code: 'yaml_parse_failed', message: 'YAML 顶层不是键值映射' }])
    }
    return { ...metadata, read_status: 'readable', ...projectFields(type, objectId, parsed, {}), issues: [] }
  } catch (error) {
    return unreadable(metadata, [{ code: 'yaml_parse_failed', message: `YAML 解析失败：${error instanceof Error ? error.message : String(error)}` }])
  }
}

function directoryStatus(scope: LocalFactScope, type: LocalFactType): LocalFactList | null {
  if (existsSync(baseDirOf(scope, type))) return null
  return { status: 'type_not_integrated', items: [], issues: [{ code: 'read_failed', message: `该类型尚未接入：缺少正式对象目录 ${path.posix.join('ldvh-base', FACT_TYPE_DIRS[type])}` }] }
}

export async function listLocalFacts(type: LocalFactType, scope: LocalFactScope): Promise<LocalFactList> {
  const missing = directoryStatus(scope, type)
  if (missing) return missing
  const entries = await readdir(baseDirOf(scope, type), { withFileTypes: true })
  const carriers = entries.filter((entry) => entry.isFile() && looksLikeFactCarrier(entry.name))
  const fileNames = carriers.filter((entry) => isExpectedCarrierName(type, entry.name)).map((entry) => entry.name).sort((left, right) => left.localeCompare(right))
  const issues = carriers.filter((entry) => !isExpectedCarrierName(type, entry.name)).map((entry) => ({
    code: 'unexpected_fact_carrier' as const,
    message: `${type} 正式载体必须是 ${type}-NNNN${FACT_TYPE_CARRIERS[type]}，已忽略错载体 ${entry.name}`,
    path: path.posix.join('ldvh-base', FACT_TYPE_DIRS[type], entry.name),
  }))
  return { status: 'complete', items: await Promise.all(fileNames.map((fileName) => readItemFile(scope, type, fileName))), issues }
}

export async function readLocalFact(type: LocalFactType, objectId: string, scope: LocalFactScope): Promise<{ status: 'ok'; item: LocalFactItem } | { status: 'not_found' | 'type_not_integrated'; metadata: LocalFactMetadata; issues: LocalFactIssue[] }> {
  const metadata = metadataFor(scope, type, objectId)
  const missing = directoryStatus(scope, type)
  if (missing) return { status: 'type_not_integrated', metadata, issues: missing.issues }
  const expectedName = expectedFileName(type, objectId)
  const entries = await readdir(baseDirOf(scope, type), { withFileTypes: true })
  if (!entries.some((entry) => entry.isFile() && entry.name === expectedName)) {
    return { status: 'not_found', metadata, issues: [{ code: 'read_failed', message: `未找到预期事实对象 ${expectedName}`, path: metadata.canonical_path }] }
  }
  return { status: 'ok', item: await readItemFile(scope, type, expectedName) }
}
