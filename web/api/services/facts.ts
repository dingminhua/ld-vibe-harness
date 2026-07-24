/** V4-only fact reader for Human-facing Web views. */

import {
  V4FactsTransportError,
} from '../internal/v4FactsTransport.js'
import { V4FactsConfigurationError } from './v4FactsConfig.js'
// 列表/详情读取已切换为本地直读，不再调用 V4 Spark machine。
import { listLocalFacts, readLocalFact, type LocalFactItem, type LocalFactMetadata, type LocalFactScope } from './localFactReader.js'
import { getWorkCaseDisplayStatus } from '../../shared/workcaseStatus.js'

export const ACTIVE_OBJECT_TYPES = ['workcase', 'adr', 'pitfall', 'spark', 'study'] as const
export const OBJECT_TYPES = ACTIVE_OBJECT_TYPES
export type ObjectType = (typeof OBJECT_TYPES)[number]

export interface WebFactResult {
  ok: true
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

function result(action: string, target: string, data: Record<string, unknown>): WebFactResult {
  return {
    ok: true,
    command: 'v4-web-facts',
    action,
    target,
    summary: { count: Array.isArray(data.items) ? data.items.length : undefined },
    issues: [],
    data,
  }
}

function error(value: unknown): WebFactError {
  if (value instanceof V4FactsTransportError) {
    return { ok: false, error: value.message, stderr: value.diagnostic, exitCode: value.code }
  }
  return { ok: false, error: value instanceof Error ? value.message : 'V4 facts unavailable', stderr: '', exitCode: 1 }
}

/** item-02：目录缺失表示该类型尚未接入；返回非空诊断项，避免与“已接入但暂无数据”混淆。 */
function notIntegrated(type: ObjectType, message: string): WebFactResult {
  const listed = result('list', type, {
    items: [{
      id: `type-not-integrated-${type}`,
      type,
      status: 'type_not_integrated',
      title: message,
      path: `ldvh-base/${type}`,
      updated: '',
      kind: 'type_not_integrated',
      message,
    }],
    coverage_status: 'type_not_integrated',
  })
  listed.issues = [{ code: 'type_not_integrated', message }]
  listed.summary.coverage_status = 'type_not_integrated'
  return listed
}

/** 精确详情的扁平 DTO：事实字段与读取元数据同时交给详情消费者。 */
function projectDetailItem(item: LocalFactItem): Record<string, unknown> {
  return {
    ...item.fact_object,
    object_ref: item.object_ref,
    canonical_path: item.canonical_path,
    absolute_path: item.absolute_path,
    carrier: item.carrier,
    check_status: item.check_status,
  }
}

/**
 * 列表只承担候选发现；不得把尚未由该消费点精确读取的 source metadata
 * 或正文载体承诺给卡片、复制和预览。
 */
function projectListItem(item: LocalFactItem): Record<string, unknown> {
  return { ...item.fact_object }
}

function readFailure(
  id: string,
  type: ObjectType,
  status: 'invalid' | 'not_found' | 'unavailable',
  metadata: LocalFactMetadata,
  issues: LocalFactItem['issues'],
): WebFactResult {
  const response = result('show', id, {
    fact_read_failure: true,
    object_ref: metadata.object_ref,
    canonical_path: metadata.canonical_path,
    absolute_path: metadata.absolute_path,
    carrier: metadata.carrier,
    check_status: status,
    read_issues: issues,
  })
  response.summary = { id, type, read_status: status }
  response.issues = issues.map((issue) => ({ ...issue }) as Record<string, unknown>)
  return response
}

export async function listObjects(type: ObjectType, _baseDir?: string, status?: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  try {
    const listed = await listLocalFacts(type, scope)
    if (listed.status !== 'complete') {
      const message = listed.issues[0]?.message ?? `类型 ${type} 尚无对象目录`
      return notIntegrated(type, message)
    }
    const projectionProblems: Array<Record<string, unknown>> = listed.items
      .filter((item) => item.check_status !== 'readable')
      .map((item) => ({
        code: 'local_read_issue',
        error: item.issues.map((issue) => issue.message).join('；'),
        object_ref: item.object_ref,
        targets: [],
      }))
    projectionProblems.push(...listed.issues.map((issue) => ({
      code: issue.code,
      error: issue.message,
      canonical_path: issue.path,
      targets: [],
    })))
    const items = listed.items
      .filter((item) => item.check_status === 'readable')
      .map(projectListItem)
      .filter((item) => !status || item.status === status)
    const response = result('list', type, {
      items,
      coverage_status: listed.status,
      projection_problems: projectionProblems,
    })
    response.issues = [
      ...listed.issues.map((issue) => ({ ...issue }) as Record<string, unknown>),
      ...listed.items.flatMap((item) => item.issues.map((issue) => ({ ...issue }) as Record<string, unknown>)),
    ]
    return response
  } catch (caught) {
    return error(caught)
  }
}

const OBJECT_ID_PATTERN = /^(workcase|adr|pitfall|spark|study)-\d+$/

export async function showObject(id: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  const match = OBJECT_ID_PATTERN.exec(id)
  if (!match) {
    return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
  }
  const type = match[1] as ObjectType
  try {
    const detail = await readLocalFact(type, id, scope)
    if (detail.status === 'not_found') return readFailure(id, type, 'not_found', detail.metadata, detail.issues)
    if (detail.status === 'type_not_integrated') {
      return readFailure(id, type, 'unavailable', detail.metadata, detail.issues)
    }
    if (detail.status === 'unavailable') {
      return readFailure(id, type, 'unavailable', detail.metadata, detail.issues)
    }
    if (detail.item.check_status !== 'readable') {
      return readFailure(id, type, 'invalid', detail.item, detail.item.issues)
    }
    const data: Record<string, unknown> = {
      ...projectDetailItem(detail.item),
      coverage_status: 'complete',
      read_issues: detail.item.issues,
    }
    const response = {
      ...result('show', id, data),
      summary: {
        id: typeof data.object_id === 'string' ? data.object_id : id,
        type: typeof data.fact_type_key === 'string' ? data.fact_type_key : type,
        status: type === 'workcase'
          ? getWorkCaseDisplayStatus(
              typeof data.phase === 'string' ? data.phase : '',
              typeof data.status === 'string' ? data.status : 'unknown',
            )
          : typeof data.status === 'string' ? data.status : 'unknown',
      },
    }
    response.issues = detail.item.issues.map((issue) => ({ ...issue }) as Record<string, unknown>)
    return response
  } catch (caught) {
    return error(caught)
  }
}

/** Non-Spark V4 readers are intentionally absent in this increment: no V2/V3 fallback or compatibility read is allowed. */
export function readFactData(_filePath: string): Record<string, unknown> {
  return {}
}

export { V4FactsConfigurationError }
